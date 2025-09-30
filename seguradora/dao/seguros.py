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

def atualizar(seguro_id: int, **campos) -> bool:
    """
    Atualiza campos do seguro. Exemplos de campos:
      - titular, valor_base, modelo, ano, placa, endereco_imovel, beneficiarios, tipo
    Retorna True se atualizou 1+ linhas.
    """
    if not campos:
        return False
    cols = []
    vals = []
    for k, v in campos.items():
        cols.append(f"{k}=?")
        vals.append(v)
    vals.append(seguro_id)
    with get_conn() as conn:
        cur = conn.execute(f"UPDATE seguros SET {', '.join(cols)} WHERE id=?", tuple(vals))
        return cur.rowcount > 0

def deletar(seguro_id: int) -> bool:
    """
    Deleta o seguro e seus vínculos (apólices e sinistros) manualmente.
    (Compatível com schema sem FK ON DELETE CASCADE)
    """
    with get_conn() as conn:
        conn.execute("BEGIN")
        ap_ids = [r["id"] for r in conn.execute("SELECT id FROM apolices WHERE seguro_id=?", (seguro_id,)).fetchall()]
        if ap_ids:
            ph = ",".join("?" * len(ap_ids))
            conn.execute(f"DELETE FROM sinistros WHERE apolice_id IN ({ph})", tuple(ap_ids))
            conn.execute(f"DELETE FROM apolices  WHERE id IN ({ph})", tuple(ap_ids))
        cur = conn.execute("DELETE FROM seguros WHERE id=?", (seguro_id,))
        conn.execute("COMMIT")
        return cur.rowcount > 0