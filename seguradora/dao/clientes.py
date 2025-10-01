from ..db import get_conn
from ..core.exceptions import AppError, CpfInvalido
from ..core import validators as val

def listar():
    with get_conn() as conn:
        return conn.execute("SELECT nome, cpf, email, telefone FROM clientes ORDER BY nome").fetchall()

def criar_cliente(dados: dict) -> int:
    cpf = val.limpar_cpf(dados.get("cpf",""))
    if not val.validar_cpf(cpf):
        raise CpfInvalido(cpf)
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO clientes (nome, cpf, data_nascimento, endereco, telefone, email) "
            "VALUES (?,?,?,?,?,?)",
            (dados["nome"], cpf, dados["data_nascimento"], dados.get("endereco"),
             dados.get("telefone"), dados.get("email"))
        )
        return cur.lastrowid

def atualizar_contato(cpf: str, telefone: str | None, email: str | None) -> bool:
    cpf = val.limpar_cpf(cpf)
    with get_conn() as conn:
        cur = conn.execute(
            "UPDATE clientes SET telefone=COALESCE(?,telefone), email=COALESCE(?,email) WHERE cpf=?",
            (telefone if telefone else None, email if email else None, cpf)
        )
        return cur.rowcount > 0

def deletar_por_cpf(cpf: str, force=False) -> bool:
    """
    Se force=True, apaga em cascata: sinistros -> apólices -> seguros do titular.
    Caso contrário, impede exclusão se houver vínculos.
    """
    cpf = val.limpar_cpf(cpf)
    with get_conn() as conn:
        vinc_apolices = conn.execute(
            "SELECT COUNT(*) AS c FROM apolices WHERE titular IN (SELECT nome FROM clientes WHERE cpf=?)", (cpf,)
        ).fetchone()["c"]
        vinc_seguros = conn.execute(
            "SELECT COUNT(*) AS c FROM seguros WHERE titular IN (SELECT nome FROM clientes WHERE cpf=?)", (cpf,)
        ).fetchone()["c"]

        if (vinc_apolices or vinc_seguros) and not force:
            raise AppError("Cliente possui vínculos.", user_message="Cliente possui apólices/seguros. Use exclusão em cascata.")

        if force:
            ap_rows = conn.execute(
                "SELECT numero FROM apolices WHERE titular IN (SELECT nome FROM clientes WHERE cpf=?)", (cpf,)
            ).fetchall()
            for r in ap_rows:
                conn.execute("DELETE FROM sinistros WHERE apolice_numero=?", (r["numero"],))
            conn.execute("DELETE FROM apolices WHERE titular IN (SELECT nome FROM clientes WHERE cpf=?)", (cpf,))
            conn.execute("DELETE FROM seguros WHERE titular IN (SELECT nome FROM clientes WHERE cpf=?)", (cpf,))

        cur = conn.execute("DELETE FROM clientes WHERE cpf=?", (cpf,))
        return cur.rowcount > 0
