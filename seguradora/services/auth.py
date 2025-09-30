# seguradora/services/auth.py
import hashlib
import sqlite3
from ..db import get_conn
from ..core.exceptions import AppError

# -------------------- bootstrap/migração de tabela (idempotente) --------------------

def _ensure_table():
    with get_conn() as conn:
        # 1) Cria uma tabela mínima se não existir (sem CHECK). Migraremos se necessário.
        conn.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                username   TEXT PRIMARY KEY,
                senha_hash TEXT NOT NULL,
                perfil     TEXT NOT NULL
                -- colunas adicionais serão checadas/ajustadas abaixo
            )
        """)

        # 2) Garante colunas ausentes (migração incremental)
        cols = {r["name"] for r in conn.execute("PRAGMA table_info(usuarios)").fetchall()}
        if "cliente_cpf" not in cols:
            conn.execute("ALTER TABLE usuarios ADD COLUMN cliente_cpf TEXT")
        if "ativo" not in cols:
            conn.execute("ALTER TABLE usuarios ADD COLUMN ativo INTEGER NOT NULL DEFAULT 1")
        if "criado_em" not in cols:
            conn.execute("ALTER TABLE usuarios ADD COLUMN criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP")

        # 3) Detecta CHECK restritivo (sem 'cliente') e migra se necessário (via DDL)
        ddl_row = conn.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name='usuarios'"
        ).fetchone()
        ddl = ddl_row["sql"] if ddl_row and ddl_row["sql"] else ""
        has_bad_check = ("CHECK" in ddl) and ("perfil IN ('admin','comum')" in ddl) and ("cliente" not in ddl)

        if has_bad_check:
            _migrate_perfil_check()

        # 4) Índice idempotente
        conn.execute("CREATE INDEX IF NOT EXISTS idx_usuarios_perfil ON usuarios(perfil)")

def _migrate_perfil_check():
    """Reconstrói a tabela 'usuarios' para aceitar perfil 'cliente'."""
    with get_conn() as conn:
        conn.executescript("""
            PRAGMA foreign_keys=OFF;

            CREATE TABLE IF NOT EXISTS usuarios__new (
                username    TEXT PRIMARY KEY,
                senha_hash  TEXT NOT NULL,
                perfil      TEXT NOT NULL,
                cliente_cpf TEXT,
                ativo       INTEGER NOT NULL DEFAULT 1,
                criado_em   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                CHECK (perfil IN ('admin','comum','cliente'))
            );

            INSERT INTO usuarios__new (username, senha_hash, perfil, cliente_cpf, ativo, criado_em)
            SELECT
                username,
                senha_hash,
                perfil,
                cliente_cpf,
                COALESCE(ativo, 1),
                COALESCE(criado_em, CURRENT_TIMESTAMP)
            FROM usuarios;

            DROP TABLE usuarios;
            ALTER TABLE usuarios__new RENAME TO usuarios;

            PRAGMA foreign_keys=ON;
        """)

_ensure_table()

# -------------------- helpers internos --------------------

def _hash_senha(senha: str) -> str:
    return hashlib.sha256(senha.encode("utf-8")).hexdigest()

def _usuario_existe(username: str) -> bool:
    with get_conn() as conn:
        row = conn.execute("SELECT 1 FROM usuarios WHERE username=?", (username,)).fetchone()
        return row is not None

def _cliente_existe(cpf: str) -> bool:
    with get_conn() as conn:
        row = conn.execute("SELECT 1 FROM clientes WHERE cpf=?", (cpf,)).fetchone()
        return row is not None

def _perfil_valido(perfil: str) -> bool:
    return perfil in ("admin", "comum", "cliente")

# -------------------- API esperada por app.py --------------------

def autenticar(username: str, senha: str):
    """
    Retorna dict {'username': ..., 'perfil': ...} se ok.
    Levanta AppError com mensagem amigável caso inválido/bloqueado.
    """
    if not username or not senha:
        raise AppError("Credenciais vazias.", user_message="Informe usuário e senha.")

    with get_conn() as conn:
        row = conn.execute(
            "SELECT username, senha_hash, perfil, ativo FROM usuarios WHERE username=?",
            (username,)
        ).fetchone()

    if not row:
        raise AppError("Usuário não encontrado.", user_message="Usuário ou senha inválidos.")

    if row["ativo"] in (0, "0", False):
        raise AppError("Usuário inativo.", user_message="Este usuário está inativo.")

    if _hash_senha(senha) != row["senha_hash"]:
        raise AppError("Senha inválida.", user_message="Usuário ou senha inválidos.")

    return {"username": row["username"], "perfil": row["perfil"]}

def criar_usuario(username: str, senha: str, perfil: str = "comum", cliente_cpf: str = None) -> bool:
    """
    Cria usuário com perfil: 'admin' | 'comum' | 'cliente'.
    Para 'cliente', exige cliente_cpf existir em clientes.
    """
    if not username or not senha:
        raise AppError("Username/senha obrigatórios.", user_message="Informe username e senha.")
    if not _perfil_valido(perfil):
        raise AppError("Perfil inválido.", user_message="Perfil deve ser admin, comum ou cliente.")
    if _usuario_existe(username):
        raise AppError("Usuário já existe.", user_message="Já existe um usuário com esse username.")

    if perfil == "cliente":
        if not cliente_cpf:
            raise AppError("CPF obrigatório para perfil cliente.", user_message="Informe um CPF de cliente.")
        if not _cliente_existe(cliente_cpf):
            raise AppError("CPF não encontrado em clientes.", user_message="CPF não existe em clientes.")

    senha_hash = _hash_senha(senha)
    sql = (
        "INSERT INTO usuarios (username, senha_hash, perfil, cliente_cpf, ativo, criado_em) "
        "VALUES (?,?,?,?,1, CURRENT_TIMESTAMP)"
    )
    args = (username, senha_hash, perfil, cliente_cpf if perfil == "cliente" else None)

    try:
        with get_conn() as conn:
            conn.execute(sql, args)
    except sqlite3.IntegrityError as e:
        # Se o banco ainda tem o CHECK antigo (sem 'cliente'), migra e tenta de novo.
        if "CHECK constraint failed" in str(e) and "perfil" in str(e):
            _migrate_perfil_check()
            with get_conn() as conn:
                conn.execute(sql, args)
        else:
            raise
    return True

# -------------------- API usada pelo menu (itens 14..17) --------------------

def criar_usuario_cliente(username: str, senha: str, cpf: str) -> bool:
    # atalho específico para o item 14
    return criar_usuario(username, senha, perfil="cliente", cliente_cpf=cpf)

def listar_usuarios():
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT username, perfil, cliente_cpf, ativo FROM usuarios ORDER BY username"
        ).fetchall()
    return rows

def editar_usuario(username: str, **campos) -> bool:
    """
    Campos aceitos:
      - senha: str
      - perfil: 'admin' | 'comum' | 'cliente'
      - ativo: bool/int
      - cliente_cpf: str (obrigatório se perfil='cliente')
    """
    if not _usuario_existe(username):
        return False

    sets, params = [], []

    # senha
    if "senha" in campos and campos["senha"]:
        sets.append("senha_hash=?")
        params.append(_hash_senha(campos["senha"]))

    # estado atual para decidir regras de cliente_cpf
    with get_conn() as conn:
        row = conn.execute(
            "SELECT perfil, cliente_cpf FROM usuarios WHERE username=?",
            (username,)
        ).fetchone()
    perfil_atual = row["perfil"] if row else None
    cliente_cpf_atual = row["cliente_cpf"] if row else None

    # perfil
    perfil = None
    if "perfil" in campos and campos["perfil"]:
        if not _perfil_valido(campos["perfil"]):
            raise AppError("Perfil inválido.", user_message="Perfil deve ser admin, comum ou cliente.")
        perfil = campos["perfil"]
        sets.append("perfil=?")
        params.append(perfil)

    # ativo
    if "ativo" in campos and campos["ativo"] is not None:
        ativo = 1 if campos["ativo"] in (True, 1, "1", "s", "S", "sim", "Sim") else 0
        sets.append("ativo=?")
        params.append(ativo)

    # cliente_cpf
    cliente_cpf = campos.get("cliente_cpf", None)
    perfil_final = perfil if perfil is not None else perfil_atual

    if perfil_final == "cliente":
        if cliente_cpf is None:
            cliente_cpf = cliente_cpf_atual
        if not cliente_cpf:
            raise AppError("Perfil 'cliente' requer CPF.", user_message="Para perfil cliente, informe um CPF.")
        if not _cliente_existe(cliente_cpf):
            raise AppError("CPF não encontrado em clientes.", user_message="CPF não existe em clientes.")
        sets.append("cliente_cpf=?")
        params.append(cliente_cpf)
    else:
        if cliente_cpf is not None:  # se enviaram cpf mas perfil não é cliente, zera
            sets.append("cliente_cpf=NULL")

    if not sets:
        return False

    params.append(username)
    with get_conn() as conn:
        cur = conn.execute(f"UPDATE usuarios SET {', '.join(sets)} WHERE username=?", params)
        return cur.rowcount > 0

def excluir_usuario(username: str) -> bool:
    with get_conn() as conn:
        cur = conn.execute("DELETE FROM usuarios WHERE username=?", (username,))
        return cur.rowcount > 0

# --- compat: alguns códigos antigos importam `_hash` direto do auth.py ---
def _hash(senha: str) -> str:
    # mantém compatibilidade com app.py antigo
    return _hash_senha(senha)
