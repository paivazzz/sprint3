from ..db import get_conn
from ..core.exceptions import AppError

def listar():
    with get_conn() as conn:
        return conn.execute("SELECT * FROM apolices ORDER BY id DESC").fetchall()

def emitir_apolice(seguro_id:int) -> str | None:
    with get_conn() as conn:
        seg = conn.execute("SELECT * FROM seguros WHERE id=?", (seguro_id,)).fetchone()
        if not seg:
            return None
        import time
        numero = f"AP-{seguro_id}-{int(time.time()*1000)}"
        valor_mensal = round(float(seg["valor_base"]) * 0.03, 2)  # exemplo
        conn.execute(
            "INSERT INTO apolices (numero,seguro_id,tipo,titular,valor_mensal,status) VALUES (?,?,?,?,?,?)",
            (numero, seg["id"], seg["tipo"], seg["titular"], valor_mensal, "Ativa")
        )
        return numero

def cancelar(numero:str) -> bool:
    with get_conn() as conn:
        ap = conn.execute("SELECT status FROM apolices WHERE numero=?", (numero,)).fetchone()
        if not ap:
            return False
        if ap["status"] == "Cancelada":
            raise AppError("Apólice já cancelada.", user_message="Esta apólice já está cancelada.")
        cur = conn.execute("UPDATE apolices SET status='Cancelada' WHERE numero=?", (numero,))
        return cur.rowcount > 0

def editar(numero:str, **campos) -> bool:
    sets, params = [], []
    for k in ("valor_mensal","titular"):
        if k in campos and campos[k] is not None:
            sets.append(f"{k}=?"); params.append(campos[k])
    if not sets:
        return False
    params.append(numero)
    with get_conn() as conn:
        cur = conn.execute(f"UPDATE apolices SET {', '.join(sets)} WHERE numero=?", params)
        return cur.rowcount > 0
