# dao/clientes.py
from datetime import datetime
from ..db import get_conn
from ..core.validators import validar_cpf
from ..core.exceptions import CpfInvalido
from ..core.exceptions import RegraNegocio

def criar_cliente(dados: dict) -> int:
    if not validar_cpf(dados["cpf"]):
        raise CpfInvalido()
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO clientes (nome,cpf,data_nascimento,endereco,telefone,email,criado_em) "
            "VALUES (?,?,?,?,?,?,?)",
            (dados["nome"], dados["cpf"], dados["data_nascimento"], dados.get("endereco"), dados.get("telefone"),
             dados.get("email"), datetime.now().isoformat(timespec="seconds"))
        )
        return cur.lastrowid

def obter_por_cpf(cpf: str):
    with get_conn() as conn:
        cur = conn.execute("SELECT * FROM clientes WHERE cpf=?", (cpf,))
        return cur.fetchone()

def atualizar_contato(cpf: str, telefone: str, email: str) -> bool:
    with get_conn() as conn:
        cur = conn.execute(
            "UPDATE clientes SET telefone=?, email=?, atualizado_em=? WHERE cpf=?",
            (telefone, email, datetime.now().isoformat(timespec="seconds"), cpf)
        )
        return cur.rowcount > 0

def listar():
    with get_conn() as conn:
        return conn.execute("SELECT * FROM clientes ORDER BY nome").fetchall()

def deletar_por_cpf(cpf: str, force: bool = False) -> bool:
    """
    Exclui um cliente por CPF.
    - Se houver seguros/apólices/sinistros vinculados, bloqueia a exclusão, a menos que force=True.
    - IMPORTANTE: este caminho usa 'seguros.titular = clientes.nome' (não há cliente_id).
    Retorna True se excluir, False se não achar o cliente.
    """
    with get_conn() as conn:
        conn.execute("BEGIN")
        cli = conn.execute("SELECT * FROM clientes WHERE cpf=?", (cpf,)).fetchone()
        if not cli:
            conn.execute("ROLLBACK")
            return False

        nome = cli["nome"]

        # seguros do titular
        seg_rows = conn.execute("SELECT id FROM seguros WHERE titular=?", (nome,)).fetchall()
        seg_ids = [r["id"] for r in seg_rows]

        if seg_ids:
            # apólices desses seguros
            placeholders = ",".join(["?"] * len(seg_ids))
            ap_rows = conn.execute(
                f"SELECT id FROM apolices WHERE seguro_id IN ({placeholders})",
                tuple(seg_ids)
            ).fetchall()
            ap_ids = [r["id"] for r in ap_rows]

            if ap_ids and not force:
                conn.execute("ROLLBACK")
                raise RegraNegocio("Cliente possui apólices/seguros vinculados. Use force=True para remover em cascata.")

            if ap_ids:
                placeholders_ap = ",".join(["?"] * len(ap_ids))
                conn.execute(
                    f"DELETE FROM sinistros WHERE apolice_id IN ({placeholders_ap})",
                    tuple(ap_ids)
                )
                conn.execute(
                    f"DELETE FROM apolices WHERE id IN ({placeholders_ap})",
                    tuple(ap_ids)
                )

            conn.execute(
                f"DELETE FROM seguros WHERE id IN ({placeholders})",
                tuple(seg_ids)
            )

        cur = conn.execute("DELETE FROM clientes WHERE cpf=?", (cpf,))
        conn.execute("COMMIT")
        return cur.rowcount > 0