# dao/sinistros.py
from datetime import datetime
from ..db import get_conn

def registrar(numero_apolice: str, descricao: str, data_ddmmaa: str) -> int | None:
    with get_conn() as conn:
        ap = conn.execute("SELECT id FROM apolices WHERE numero=? AND status='Ativa'", (numero_apolice,)).fetchone()
        if not ap:
            return None
        cur = conn.execute(
            "INSERT INTO sinistros (apolice_id,descricao,data,status,criado_em) VALUES (?,?,?,?,?)",
            (ap["id"], descricao, data_ddmmaa, "Aberto", datetime.now().isoformat(timespec="seconds"))
        )
        return cur.lastrowid

def fechar(numero_apolice: str) -> bool:
    with get_conn() as conn:
        cur = conn.execute(
            "UPDATE sinistros SET status='Fechado', fechado_em=? "
            "WHERE apolice_id=(SELECT id FROM apolices WHERE numero=?) AND status='Aberto'",
            (datetime.now().isoformat(timespec="seconds"), numero_apolice)
        )
        return cur.rowcount > 0

def listar():
    with get_conn() as conn:
        return conn.execute(
            "SELECT si.*, a.numero AS apolice_numero FROM sinistros si JOIN apolices a ON a.id=si.apolice_id ORDER BY si.criado_em DESC"
        ).fetchall()

# seguradora/dao/sinistros.py
from ..db import get_conn

def editar_por_id(sinistro_id: int, **campos) -> bool:
    """
    Edita sinistro pelo ID.
    Campos comuns: descricao, data (DD/MM/AAAA), status ('Aberto'/'Fechado')
    """
    if not campos:
        return False
    cols, vals = [], []
    for k, v in campos.items():
        cols.append(f"{k}=?"); vals.append(v)
    vals.append(sinistro_id)
    with get_conn() as conn:
        cur = conn.execute(f"UPDATE sinistros SET {', '.join(cols)} WHERE id=?", tuple(vals))
        return cur.rowcount > 0
