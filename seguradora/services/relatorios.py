# services/relatorios.py
import csv, json
from pathlib import Path
from ..db import get_conn

EXPORT_DIR = Path("exports")
EXPORT_DIR.mkdir(exist_ok=True)

def receita_mensal_prevista():
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT strftime('%Y-%m', criado_em) AS ym, SUM(valor_mensal) AS receita "
            "FROM apolices WHERE status='Ativa' GROUP BY ym ORDER BY ym DESC"
        ).fetchall()
    return rows

def top_clientes_por_valor_segurado(limit=5):
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT s.titular AS cliente, SUM(s.valor_base) AS total "
            "FROM apolices a JOIN seguros s ON s.id=a.seguro_id "
            "WHERE a.status='Ativa' GROUP BY s.titular ORDER BY total DESC LIMIT ?",
            (limit,)
        ).fetchall()
    return rows

def sinistros_por_status():
    with get_conn() as conn:
        return conn.execute(
            "SELECT status, COUNT(*) AS qtd FROM sinistros GROUP BY status"
        ).fetchall()

def sinistros_por_periodo(ym_ini: str, ym_fim: str):
    # ym = 'YYYY-MM'
    with get_conn() as conn:
        return conn.execute(
            "SELECT strftime('%Y-%m', criado_em) AS ym, COUNT(*) AS qtd "
            "FROM sinistros WHERE ym BETWEEN ? AND ? GROUP BY ym ORDER BY ym",
            (ym_ini, ym_fim)
        ).fetchall()

def export_csv(nome: str, rows):
    path = EXPORT_DIR / f"{nome}.csv"
    if not rows:
        path.write_text("")
        return str(path)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    return str(path)

def export_json(nome: str, rows):
    path = EXPORT_DIR / f"{nome}.json"
    with path.open("w", encoding="utf-8") as f:
        json.dump([dict(r) for r in rows], f, ensure_ascii=False, indent=2)
    return str(path)
