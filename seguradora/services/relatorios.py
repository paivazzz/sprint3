# seguradora/services/relatorios.py
import csv
import json
from pathlib import Path
from datetime import datetime
from ..db import get_conn

EXPORT_DIR = Path("exports")
EXPORT_DIR.mkdir(exist_ok=True)

def receita_mensal_prevista():
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT strftime('%Y-%m', criado_em) AS ym, SUM(valor_mensal) AS receita "
            "FROM apolices "
            "WHERE status='Ativa' "
            "GROUP BY ym "
            "ORDER BY ym DESC"
        ).fetchall()
    return rows

def top_clientes_por_valor_segurado(limit=5):
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT s.titular AS cliente, SUM(s.valor_base) AS total "
            "FROM apolices a "
            "JOIN seguros s ON s.id = a.seguro_id "
            "WHERE a.status='Ativa' "
            "GROUP BY s.titular "
            "ORDER BY total DESC "
            "LIMIT ?",
            (limit,)
        ).fetchall()
    return rows

def sinistros_por_status():
    with get_conn() as conn:
        return conn.execute(
            "SELECT status, COUNT(*) AS qtd "
            "FROM sinistros "
            "GROUP BY status"
        ).fetchall()

def sinistros_por_periodo(ym_ini: str, ym_fim: str):
    """
    ym_ini / ym_fim no formato 'YYYY-MM'.
    Usa strftime no WHERE (não pode usar alias da SELECT no WHERE em SQLite).
    """
    with get_conn() as conn:
        return conn.execute(
            "SELECT strftime('%Y-%m', criado_em) AS ym, COUNT(*) AS qtd "
            "FROM sinistros "
            "WHERE strftime('%Y-%m', criado_em) BETWEEN ? AND ? "
            "GROUP BY ym "
            "ORDER BY ym",
            (ym_ini, ym_fim)
        ).fetchall()

def export_csv(nome: str, rows):
    """
    Exporta para CSV em exports/<nome>.csv aceitando:
      - lista de dicts
      - lista de sqlite3.Row (tem .keys())
      - lista de tuplas/listas
      - lista simples (uma coluna)
    Evita o erro do DictWriter usando extrasaction='ignore'.
    """
    path = EXPORT_DIR / f"{nome}.csv"

    # nada para exportar: cria arquivo vazio (UX consistente)
    if not rows:
        path.write_text("")
        return str(path)

    first = rows[0]

    with path.open("w", newline="", encoding="utf-8") as f:
        # 1) lista de dicts
        if isinstance(first, dict):
            fieldnames = list(first.keys())
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(rows)
            return str(path)

        # 2) objetos tipo sqlite3.Row (têm .keys())
        if hasattr(first, "keys"):
            headers = list(first.keys())
            w = csv.writer(f)
            w.writerow(headers)
            for r in rows:
                w.writerow([r[h] for h in headers])
            return str(path)

        # 3) lista de tuplas/listas (já estruturado)
        if isinstance(first, (tuple, list)):
            w = csv.writer(f)
            w.writerows(rows)
            return str(path)

        # 4) lista simples (uma coluna)
        w = csv.writer(f)
        for r in rows:
            w.writerow([r])

    return str(path)

def export_json(nome: str, rows):
    """
    Exporta para JSON em exports/<nome>.json aceitando os mesmos formatos do CSV.
    """
    path = EXPORT_DIR / f"{nome}.json"

    with path.open("w", encoding="utf-8") as f:
        if not rows:
            json.dump([], f, ensure_ascii=False, indent=2)
            return str(path)

        first = rows[0]

        if isinstance(first, dict):
            json.dump(rows, f, ensure_ascii=False, indent=2)
        elif hasattr(first, "keys"):  # sqlite3.Row
            json.dump([dict(r) for r in rows], f, ensure_ascii=False, indent=2)
        elif isinstance(first, (tuple, list)):
            json.dump(rows, f, ensure_ascii=False, indent=2)
        else:
            # lista simples
            json.dump(list(rows), f, ensure_ascii=False, indent=2)

    return str(path)
# seguradora/services/relatorios.py
import csv
import json
from pathlib import Path
from datetime import datetime
from ..db import get_conn

EXPORT_DIR = Path("exports")
EXPORT_DIR.mkdir(exist_ok=True)

def receita_mensal_prevista():
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT strftime('%Y-%m', criado_em) AS ym, SUM(valor_mensal) AS receita "
            "FROM apolices "
            "WHERE status='Ativa' "
            "GROUP BY ym "
            "ORDER BY ym DESC"
        ).fetchall()
    return rows

def top_clientes_por_valor_segurado(limit=5):
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT s.titular AS cliente, SUM(s.valor_base) AS total "
            "FROM apolices a "
            "JOIN seguros s ON s.id = a.seguro_id "
            "WHERE a.status='Ativa' "
            "GROUP BY s.titular "
            "ORDER BY total DESC "
            "LIMIT ?",
            (limit,)
        ).fetchall()
    return rows

def sinistros_por_status():
    with get_conn() as conn:
        return conn.execute(
            "SELECT status, COUNT(*) AS qtd "
            "FROM sinistros "
            "GROUP BY status"
        ).fetchall()

def sinistros_por_periodo(ym_ini: str, ym_fim: str):
    """
    ym_ini / ym_fim no formato 'YYYY-MM'.
    Usa strftime no WHERE (não pode usar alias da SELECT no WHERE em SQLite).
    """
    with get_conn() as conn:
        return conn.execute(
            "SELECT strftime('%Y-%m', criado_em) AS ym, COUNT(*) AS qtd "
            "FROM sinistros "
            "WHERE strftime('%Y-%m', criado_em) BETWEEN ? AND ? "
            "GROUP BY ym "
            "ORDER BY ym",
            (ym_ini, ym_fim)
        ).fetchall()

def export_csv(nome: str, rows):
    """
    Exporta para CSV em exports/<nome>.csv aceitando:
      - lista de dicts
      - lista de sqlite3.Row (tem .keys())
      - lista de tuplas/listas
      - lista simples (uma coluna)
    Evita o erro do DictWriter usando extrasaction='ignore'.
    """
    path = EXPORT_DIR / f"{nome}.csv"

    # nada para exportar: cria arquivo vazio (UX consistente)
    if not rows:
        path.write_text("")
        return str(path)

    first = rows[0]

    with path.open("w", newline="", encoding="utf-8") as f:
        # 1) lista de dicts
        if isinstance(first, dict):
            fieldnames = list(first.keys())
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(rows)
            return str(path)

        # 2) objetos tipo sqlite3.Row (têm .keys())
        if hasattr(first, "keys"):
            headers = list(first.keys())
            w = csv.writer(f)
            w.writerow(headers)
            for r in rows:
                w.writerow([r[h] for h in headers])
            return str(path)

        # 3) lista de tuplas/listas (já estruturado)
        if isinstance(first, (tuple, list)):
            w = csv.writer(f)
            w.writerows(rows)
            return str(path)

        # 4) lista simples (uma coluna)
        w = csv.writer(f)
        for r in rows:
            w.writerow([r])

    return str(path)

def export_json(nome: str, rows):
    """
    Exporta para JSON em exports/<nome>.json aceitando os mesmos formatos do CSV.
    """
    path = EXPORT_DIR / f"{nome}.json"

    with path.open("w", encoding="utf-8") as f:
        if not rows:
            json.dump([], f, ensure_ascii=False, indent=2)
            return str(path)

        first = rows[0]

        if isinstance(first, dict):
            json.dump(rows, f, ensure_ascii=False, indent=2)
        elif hasattr(first, "keys"):  # sqlite3.Row
            json.dump([dict(r) for r in rows], f, ensure_ascii=False, indent=2)
        elif isinstance(first, (tuple, list)):
            json.dump(rows, f, ensure_ascii=False, indent=2)
        else:
            # lista simples
            json.dump(list(rows), f, ensure_ascii=False, indent=2)

    return str(path)
