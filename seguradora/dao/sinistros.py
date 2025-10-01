from ..db import get_conn
from ..core.exceptions import AppError
from ..core import validators as val

def listar():
    with get_conn() as conn:
        return conn.execute("SELECT * FROM sinistros ORDER BY id DESC").fetchall()

def registrar(apolice_numero:str, descricao:str, data_ddmmaa:str) -> int | None:
    if not val.validar_data_ddmmaa(data_ddmmaa):
        raise AppError("Data inválida.", user_message="Data inválida. Use DD/MM/AAAA.")
    with get_conn() as conn:
        ap = conn.execute("SELECT numero,status FROM apolices WHERE numero=?", (apolice_numero,)).fetchone()
        if not ap or ap["status"] != "Ativa":
            return None
        cur = conn.execute(
            "INSERT INTO sinistros (apolice_numero, descricao, data, status) VALUES (?,?,?, 'Aberto')",
            (apolice_numero, descricao, data_ddmmaa)
        )
        return cur.lastrowid

def fechar(apolice_numero:str) -> bool:
    with get_conn() as conn:
        abertos = conn.execute(
            "SELECT id FROM sinistros WHERE apolice_numero=? AND status='Aberto'", (apolice_numero,)
        ).fetchall()
        if not abertos:
            return False
        cur = conn.execute(
            "UPDATE sinistros SET status='Fechado' WHERE apolice_numero=? AND status='Aberto'",
            (apolice_numero,)
        )
        return cur.rowcount > 0

def editar(sinistro_id:int, **campos) -> bool:
    """
    Campos: descricao, data (DD/MM/AAAA), status ('Aberto'|'Fechado')
    """
    sets, params = [], []
    if "descricao" in campos and campos["descricao"] is not None:
        sets.append("descricao=?"); params.append(campos["descricao"])
    if "data" in campos and campos["data"] is not None:
        if not val.validar_data_ddmmaa(campos["data"]):
            raise AppError("Data inválida.", user_message="Data inválida. Use DD/MM/AAAA.")
        sets.append("data=?"); params.append(campos["data"])
    if "status" in campos and campos["status"] is not None:
        if campos["status"] not in ("Aberto","Fechado"):
            raise AppError("Status inválido.", user_message="Status deve ser Aberto ou Fechado.")
        sets.append("status=?"); params.append(campos["status"])

    if not sets:
        return False
    params.append(sinistro_id)
    with get_conn() as conn:
        cur = conn.execute(f"UPDATE sinistros SET {', '.join(sets)} WHERE id=?", params)
        return cur.rowcount > 0
