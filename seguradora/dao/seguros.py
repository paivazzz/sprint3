# dao/seguros.py
from datetime import datetime
from ..db import get_conn

def criar_seguro_automovel(titular, valor_base, modelo, ano, placa) -> int:
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO seguros (titular,tipo,valor_base,modelo,ano,placa,criado_em) "
            "VALUES (?,?,?,?,?,?,?)",
            (titular, "Automóvel", valor_base, modelo, ano, placa, datetime.now().isoformat(timespec="seconds"))
        )
        return cur.lastrowid

def criar_seguro_residencial(titular, valor_base, endereco_imovel) -> int:
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO seguros (titular,tipo,valor_base,endereco_imovel,criado_em) VALUES (?,?,?,?,?)",
            (titular, "Residencial", valor_base, endereco_imovel, datetime.now().isoformat(timespec="seconds"))
        )
        return cur.lastrowid

def criar_seguro_vida(titular, valor_base, beneficiarios_csv) -> int:
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO seguros (titular,tipo,valor_base,beneficiarios,criado_em) VALUES (?,?,?,?,?)",
            (titular, "Vida", valor_base, beneficiarios_csv, datetime.now().isoformat(timespec="seconds"))
        )
        return cur.lastrowid

def obter(seguro_id: int):
    with get_conn() as conn:
        return conn.execute("SELECT * FROM seguros WHERE id=?", (seguro_id,)).fetchone()

def listar():
    with get_conn() as conn:
        return conn.execute("SELECT * FROM seguros ORDER BY criado_em DESC").fetchall()
