from ..db import get_conn

def registrar(username: str, operacao: str, entidade: str, entidade_id, ok: bool, detalhes: str | None):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO auditoria (username, operacao, entidade, entidade_id, ok, detalhes) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (username, operacao, entidade, str(entidade_id) if entidade_id is not None else None,
             1 if ok else 0, detalhes)
        )
