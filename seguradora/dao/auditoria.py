# dao/auditoria.py
from datetime import datetime
from ..db import get_conn

def registrar(usuario, operacao, entidade, entidade_id, sucesso, detalhes=None):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO auditoria (timestamp,usuario,operacao,entidade,entidade_id,sucesso,detalhes) "
            "VALUES (?,?,?,?,?,?,?)",
            (datetime.now().isoformat(timespec="seconds"), usuario, operacao, entidade, str(entidade_id) if entidade_id else None, int(sucesso), detalhes)
        )
