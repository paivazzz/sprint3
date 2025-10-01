from ..db import get_conn
from ..core.exceptions import AppError

def listar():
    with get_conn() as conn:
        return conn.execute("SELECT * FROM seguros ORDER BY id DESC").fetchall()

def criar_seguro_automovel(titular:str, valor:float, modelo:str, ano:int, placa:str) -> int:
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO seguros (tipo,titular,valor_base,modelo,ano,placa) VALUES (?,?,?,?,?,?)",
            ("Automóvel", titular, valor, modelo, ano, placa)
        )
        return cur.lastrowid

def criar_seguro_residencial(titular:str, valor:float, endereco_imovel:str) -> int:
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO seguros (tipo,titular,valor_base,endereco_imovel) VALUES (?,?,?,?)",
            ("Residencial", titular, valor, endereco_imovel)
        )
        return cur.lastrowid

def criar_seguro_vida(titular:str, valor:float, beneficiarios:str) -> int:
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO seguros (tipo,titular,valor_base,beneficiarios) VALUES (?,?,?,?)",
            ("Vida", titular, valor, beneficiarios)
        )
        return cur.lastrowid

def editar_seguro(seguro_id:int, **campos) -> bool:
    sets, params = [], []
    for k in ("titular","valor_base","modelo","ano","placa","endereco_imovel","beneficiarios"):
        if k in campos and campos[k] is not None:
            sets.append(f"{k}=?"); params.append(campos[k])
    if not sets:
        return False
    params.append(seguro_id)
    with get_conn() as conn:
        cur = conn.execute(f"UPDATE seguros SET {', '.join(sets)} WHERE id=?", params)
        return cur.rowcount > 0

def deletar_seguro(seguro_id:int) -> bool:
    with get_conn() as conn:
        ap = conn.execute("SELECT COUNT(*) c FROM apolices WHERE seguro_id=?", (seguro_id,)).fetchone()["c"]
        if ap:
            raise AppError("Seguro vinculado a apólice.", user_message="Existe apólice para esse seguro. Cancele/exclua antes.")
        cur = conn.execute("DELETE FROM seguros WHERE id=?", (seguro_id,))
        return cur.rowcount > 0
