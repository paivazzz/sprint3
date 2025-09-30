# dao/apolices.py
from datetime import datetime
from ..db import get_conn

def calcular_valor_mensal(tipo: str, valor_base: float) -> float:
    return {
        "Automóvel": 0.03,
        "Residencial": 0.01,
        "Vida": 0.015
    }[tipo] * float(valor_base)

def proximo_numero(conn) -> str:
    # simples: numero com 5 dígitos sequenciais
    cur = conn.execute("SELECT COUNT(*) AS c FROM apolices")
    c = cur.fetchone()["c"]
    return f"{(c+1):05d}"

def emitir_apolice(seguro_id: int) -> str:
    with get_conn() as conn:
        seg = conn.execute("SELECT tipo, valor_base FROM seguros WHERE id=?", (seguro_id,)).fetchone()
        if not seg:
            return None
        numero = proximo_numero(conn)
        valor_mensal = calcular_valor_mensal(seg["tipo"], seg["valor_base"])
        conn.execute(
            "INSERT INTO apolices (numero,seguro_id,valor_mensal,status,criado_em) VALUES (?,?,?,?,?)",
            (numero, seguro_id, valor_mensal, "Ativa", datetime.now().isoformat(timespec="seconds"))
        )
        return numero

def cancelar(numero: str) -> bool:
    with get_conn() as conn:
        cur = conn.execute("UPDATE apolices SET status='Cancelada', cancelado_em=? WHERE numero=? AND status='Ativa'",
                           (datetime.now().isoformat(timespec="seconds"), numero))
        return cur.rowcount > 0

def obter_por_numero(numero: str):
    with get_conn() as conn:
        return conn.execute(
            "SELECT a.*, s.titular, s.tipo, s.valor_base FROM apolices a JOIN seguros s ON s.id=a.seguro_id WHERE a.numero=?",
            (numero,)
        ).fetchone()

def listar():
    with get_conn() as conn:
        return conn.execute(
            "SELECT a.*, s.titular, s.tipo FROM apolices a JOIN seguros s ON s.id=a.seguro_id ORDER BY a.criado_em DESC"
        ).fetchall()

# seguradora/dao/apolices.py
from ..db import get_conn

def editar(numero: int, **campos) -> bool:
    """
    Edita apólice por número. Campos comuns:
      - valor_mensal (float), status ('Ativa'/'Cancelada'), validade_inicial, validade_final
    Regra simples: se já estiver 'Cancelada', impedir voltar pra 'Ativa' (exemplo).
    """
    if not campos:
        return False
    if "status" in campos and campos["status"] == "Ativa":
        # exemplo de regra: não reativar cancelada
        with get_conn() as conn:
            ap = conn.execute("SELECT status FROM apolices WHERE numero=?", (numero,)).fetchone()
            if ap and ap["status"] == "Cancelada":
                return False
    cols, vals = [], []
    for k, v in campos.items():
        cols.append(f"{k}=?"); vals.append(v)
    vals.append(numero)
    with get_conn() as conn:
        cur = conn.execute(f"UPDATE apolices SET {', '.join(cols)} WHERE numero=?", tuple(vals))
        return cur.rowcount > 0
