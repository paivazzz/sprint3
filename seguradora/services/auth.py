# services/auth.py
import hashlib
from datetime import datetime
from ..db import get_conn

def _hash(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

def criar_usuario(username: str, senha: str, perfil: str):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO usuarios (username, senha_hash, perfil, criado_em) VALUES (?,?,?,?)",
            (username, _hash(senha), perfil, datetime.now().isoformat(timespec="seconds"))
        )

def autenticar(username: str, senha: str):
    with get_conn() as conn:
        row = conn.execute("SELECT username, senha_hash, perfil FROM usuarios WHERE username=?", (username,)).fetchone()
        if not row or row["senha_hash"] != _hash(senha):
            return None
        return {"username": row["username"], "perfil": row["perfil"]}
