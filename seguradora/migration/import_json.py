# migration/import_json.py
import json
from pathlib import Path
from datetime import datetime
from ..db import get_conn
from ..dao import clientes as cli_dao, seguros as se_dao, apolices as ap_dao, sinistros as si_dao

# caminhos esperados (ajuste se necessário)
JSONS = {
    "clientes": Path("clientes.json"),
    "seguros": Path("seguros.json"),
    "apolices": Path("apolices.json"),
    "sinistros": Path("sinistros.json"),
}

def exists_all():
    return all(p.exists() for p in JSONS.values())

def run():
    if not exists_all():
        print("Arquivos JSON não encontrados ao lado do projeto (clientes/seguros/apolices/sinistros).")
        return

    # clientes
    data = json.loads(JSONS["clientes"].read_text(encoding="utf-8"))
    for c in data:
        # compatível com sprint 2: nome, cpf, datanascimento, endereco, telefone, email
        try:
            cli_dao.criar_cliente({
                "nome": c["nome"],
                "cpf": c["cpf"],
                "data_nascimento": c.get("datanascimento") or c.get("data_nascimento") or "01/01/2000",
                "endereco": c.get("endereco"),
                "telefone": c.get("telefone"),
                "email": c.get("email")
            })
        except Exception:
            pass

    # seguros
    segs = json.loads(JSONS["seguros"].read_text(encoding="utf-8"))
    id_map = {}  # mapeia índice antigo -> id novo
    for idx, s in enumerate(segs):
        tipo = s["tipo"]
        titular = s["titular"]
        valor = float(s.get("valor") or s.get("valor_base") or 0)
        if tipo == "Automóvel":
            sid = se_dao.criar_seguro_automovel(titular, valor, s.get("modelo"), int(s.get("ano") or 0), s.get("placa"))
        elif tipo == "Residencial":
            sid = se_dao.criar_seguro_residencial(titular, valor, s.get("endereco"))
        elif tipo == "Vida":
            benef = ",".join(s.get("beneficiarios", []))
            sid = se_dao.criar_seguro_vida(titular, valor, benef)
        else:
            continue
        id_map[idx] = sid

    # apólices
    aps = json.loads(JSONS["apolices"].read_text(encoding="utf-8"))
    for a in aps:
        # precisamos do seguro correspondente; se não tiver ID, tente casar por titular/tipo/valor
        sid = None
        if "seguro_index" in a and a["seguro_index"] in id_map:
            sid = id_map[a["seguro_index"]]
        if sid is None:
            # fallback simples
            pass
        if sid:
            ap_dao.emitir_apolice(sid)

    # sinistros
    sis = json.loads(JSONS["sinistros"].read_text(encoding="utf-8"))
    for s in sis:
        numero = s.get("apolice_numero") or s.get("apolice", {}).get("numero")
        descricao = s.get("descricao")
        data = s.get("data")
        if numero and descricao and data:
            sid = si_dao.registrar(numero, descricao, data)
            if s.get("status") == "Fechado":
                from ..dao.sinistros import fechar
                fechar(numero)

    print("Migração concluída.")
