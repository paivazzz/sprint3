# dao/clientes.py
from datetime import datetime
from ..db import get_conn
from ..core.validators import validar_cpf
from ..core.exceptions import CpfInvalido

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
