from ..core.exceptions import AppError, OperacaoNaoPermitida
from ..core.logging_conf import setup_logging
from ..services import auth, relatorios
from ..dao import clientes as cli_dao, seguros as se_dao, apolices as ap_dao, sinistros as si_dao
from ..dao import auditoria as aud
from .prompts import yesno, ask, buscar_por_cpf, buscar_por_numero_apolice
from datetime import datetime

logger = setup_logging()

def _audit(usuario, op, entidade, entidade_id, ok, detalhes=None):
    aud.registrar(usuario["username"], op, entidade, entidade_id, ok, detalhes)

def _guard(perfil_ativo, precisa_admin=False):
    if precisa_admin and perfil_ativo != "admin":
        raise OperacaoNaoPermitida()

def _submenu_relatorios():
    last = []
    while True:
        print("\n— Relatórios —")
        print("[1] Receita mensal prevista")
        print("[2] Top clientes por valor segurado")
        print("[3] Sinistros por status")
        print("[4] Sinistros por período (YYYY-MM a YYYY-MM)")
        print("[5] Exportar último resultado (CSV)")
        print("[0] Voltar")
        sub = input("Escolha: ").strip()

        try:
            if sub == "1":
                rows = relatorios.receita_mensal_prevista()
                last = rows
                for r in rows:
                    valor = r['receita'] if r['receita'] is not None else 0
                    print(f"{r['ym']}: R${valor:.2f}")
                if yesno("Exportar agora para CSV?"):
                    caminho = relatorios.export_csv(f"rel_{datetime.now().strftime('%Y%m%d_%H%M%S')}", rows)
                    print(f"Exportado: {caminho}")

            elif sub == "2":
                rows = relatorios.top_clientes_por_valor_segurado()
                last = rows
                for r in rows:
                    print(f"{r['cliente']}: R${r['total']:.2f}")
                if yesno("Exportar agora para CSV?"):
                    caminho = relatorios.export_csv(f"rel_{datetime.now().strftime('%Y%m%d_%H%M%S')}", rows)
                    print(f"Exportado: {caminho}")

            elif sub == "3":
                rows = relatorios.sinistros_por_status()
                last = rows
                for r in rows:
                    print(f"{r['status']}: {r['qtd']}")
                if yesno("Exportar agora para CSV?"):
                    caminho = relatorios.export_csv(f"rel_{datetime.now().strftime('%Y%m%d_%H%M%S')}", rows)
                    print(f"Exportado: {caminho}")

            elif sub == "4":
                ini = input("De (YYYY-MM): ").strip()
                fim = input("Até (YYYY-MM): ").strip()
                rows = relatorios.sinistros_por_periodo(ini, fim)
                last = rows
                for r in rows:
                    print(f"{r['ym']}: {r['qtd']} sinistro(s)")
                if yesno("Exportar agora para CSV?"):
                    caminho = relatorios.export_csv(f"rel_{datetime.now().strftime('%Y%m%d_%H%M%S')}", rows)
                    print(f"Exportado: {caminho}")

            elif sub == "5":
                if last:
                    caminho = relatorios.export_csv(f"rel_{datetime.now().strftime('%Y%m%d_%H%M%S')}", last)
                    print(f"Exportado: {caminho}")
                else:
                    print("Nada para exportar ainda.")
            elif sub == "0":
                break
            else:
                print("Opção inválida.")
        except AppError as e:
            print(e.user_message)
            logger.error(f"erro de negócio relatorio: {e}")
        except Exception as e:
            print("Algo deu errado ao gerar/exportar relatório.")
            logger.exception(f"erro inesperado relatorio: {e}")

def _listar_usuarios_flow(usuario):
    rows = auth.listar_usuarios()
    print("\n— Usuários —")
    for r in rows:
        ativo = "Ativo" if r["ativo"] in (1,"1",True) else "Inativo"
        print(f"{r['username']} | Perfil: {r['perfil']} | {ativo}")

def _cadastrar_usuario_cliente_flow(usuario):
    print("\n— Cadastrar Usuário (cliente) —")
    username = ask("Username: ")
    senha = ask("Senha: ")
    cpf = buscar_por_cpf()
    try:
        ok = auth.criar_usuario_cliente(username, senha, cpf)
        if ok:
            print("Usuário (cliente) criado.")
            logger.info(f"usuario cliente criado username={username} cpf={cpf}")
            _audit(usuario, "criar", "usuario", username, True, f"perfil=cliente cpf={cpf}")
    except AppError as e:
        print(e.user_message); logger.error(f"erro negocio criar usuario cliente: {e}")
        _audit(usuario, "criar", "usuario", username, False, e.user_message)
    except Exception as e:
        print("Erro ao cadastrar usuário.")
        logger.exception(f"erro inesperado criar usuario cliente: {e}")
        _audit(usuario, "criar", "usuario", username, False, "erro inesperado")

def _editar_usuario_flow(usuario):
    print("\n— Editar Usuário —")
    username = ask("Username: ")
    alterar_senha = yesno("Alterar senha?")
    senha = ask("Nova senha: ", required=False) if alterar_senha else None
    perfil = ask("Perfil (admin/comum/cliente) [enter p/ manter]: ", required=False)
    ativo_raw = ask("Ativo? (s/N) [enter p/ manter]: ", required=False)
    ativo = None if not ativo_raw else (ativo_raw.lower() in ("s","sim","y","yes","1"))
    cliente_cpf = None
    if (perfil and perfil == "cliente") or yesno("Deseja informar/alterar CPF de cliente?"):
        cliente_cpf = buscar_por_cpf()
    try:
        ok = auth.editar_usuario(username, senha=senha, perfil=perfil or None, ativo=ativo, cliente_cpf=cliente_cpf)
        print("Atualizado." if ok else "Usuário não encontrado ou nada a alterar.")
        _audit(usuario, "editar", "usuario", username, bool(ok))
    except AppError as e:
        print(e.user_message); logger.error(f"erro negocio editar usuario: {e}")
        _audit(usuario, "editar", "usuario", username, False, e.user_message)
    except Exception as e:
        print("Erro ao editar usuário.")
        logger.exception(f"erro inesperado editar usuario: {e}")
        _audit(usuario, "editar", "usuario", username, False, "erro inesperado")

def _excluir_usuario_flow(usuario):
    print("\n— Excluir Usuário —")
    username = ask("Username: ")
    if not yesno(f"Confirmar exclusão do usuário {username}?"):
        print("Exclusão cancelada.")
        return
    try:
        ok = auth.excluir_usuario(username)
        print("Usuário excluído." if ok else "Usuário não encontrado.")
        _audit(usuario, "excluir", "usuario", username, bool(ok))
    except Exception as e:
        print("Erro ao excluir usuário.")
        logger.exception(f"erro inesperado excluir usuario: {e}")
        _audit(usuario, "excluir", "usuario", username, False, "erro inesperado")

def loop_principal(sessao):
    perfil = sessao["perfil"]
    usuario = {"username": sessao["username"], "perfil": perfil}

    while True:
        print("\n=== MENU ===")
        print("[1] Listar Clientes                  [2] Listar Seguros                   [3] Listar Apólices                  [4] Listar Sinistros")
        if perfil == "admin":
            print("[5] Cadastrar Cliente                [6] Cadastrar Seguro                 [7] Emitir Apólice                   [8] Registrar Sinistro")
            print("[9] Editar Cliente                   [10] Cancelar Apólice                [11] Fechar Sinistro                 [12] Relatórios")
            print("[13] Excluir Cliente                 [14] Cadastrar Usuário (cliente)     [15] Listar Usuários                 [16] Editar Usuário")
            print("[17] Excluir Usuário                 [18] Editar Seguro                    [19] Excluir Seguro                  [20] Editar Apólice")
            print("[21] Editar Sinistro                 [0] Sair")
        else:
            print("[12] Relatórios                      [0] Sair")

        op = input("Escolha uma opção: ").strip()

        # atalhos de busca rápida
        ol = op.lower()
        if ol.startswith("cpf:"):
            chave = op[4:].strip()
            rows = cli_dao.listar()
            achou = False
            for r in rows:
                if chave in r["cpf"]:
                    print(f"{r['nome']} | CPF: {r['cpf']} | Email: {r['email'] or '-'} | Tel: {r['telefone'] or '-'}")
                    achou = True
            if not achou:
                print("Nenhum cliente encontrado para esse CPF.")
            continue

        if ol.startswith("apolice:") or ol.startswith("apólice:"):
            chave = op.split(":",1)[1].strip()
            rows = ap_dao.listar()
            achou = False
            for a in rows:
                if chave in a["numero"]:
                    print(f"Nº {a['numero']} | {a['tipo']} | Titular: {a['titular']} | Mensal: R${a['valor_mensal']:.2f} | {a['status']}")
                    achou = True
            if not achou:
                print("Nenhuma apólice encontrada para esse número.")
            continue

        if ol.startswith("nome:"):
            chave = op[5:].strip().lower()
            rows = cli_dao.listar()
            achou = False
            for r in rows:
                if chave in r["nome"].lower():
                    print(f"{r['nome']} | CPF: {r['cpf']} | Email: {r['email'] or '-'} | Tel: {r['telefone'] or '-'}")
                    achou = True
            if not achou:
                print("Nenhum cliente encontrado para esse nome.")
            continue

        try:
            # VISÃO COMUM (consultas/relatórios)
            if op == "1":
                rows = cli_dao.listar()
                print("\n— Clientes —")
                for r in rows:
                    print(f"{r['nome']} | CPF: {r['cpf']} | Email: {r['email'] or '-'} | Tel: {r['telefone'] or '-'}")

            elif op == "2":
                rows = se_dao.listar()
                print("\n— Seguros —")
                for r in rows:
                    extra = ""
                    if r["tipo"] == "Automóvel":
                        extra = f"{r['modelo'] or ''} {r['ano'] or ''} ({r['placa'] or ''})"
                    elif r["tipo"] == "Residencial":
                        extra = r["endereco_imovel"] or ""
                    elif r["tipo"] == "Vida":
                        extra = f"Benef: {r['beneficiarios'] or ''}"
                    print(f"#{r['id']} {r['tipo']} | Titular: {r['titular']} | Valor base: R${r['valor_base']:.2f} {extra}")

            elif op == "3":
                rows = ap_dao.listar()
                print("\n— Apólices —")
                for a in rows:
                    print(f"Nº {a['numero']} | {a['tipo']} | Titular: {a['titular']} | Mensal: R${a['valor_mensal']:.2f} | {a['status']}")

            elif op == "4":
                rows = si_dao.listar()
                print("\n— Sinistros —")
                for s in rows:
                    print(f"ID {s['id']} | Apólice {s['apolice_numero']} | {s['data']} | {s['status']} | {s['descricao']}")

            elif op == "12":
                _submenu_relatorios()

            elif op == "0":
                print("Encerrando...")
                break

            # ITENS ADMIN
            elif perfil == "admin" and op == "5":
                nome = ask("Nome: ")
                cpf = ask("CPF: ")
                data_nasc = ask("Data de nascimento (DD/MM/AAAA): ")
                end = ask("Endereço: ", required=False)
                tel = ask("Telefone: ", required=False)
                email = ask("Email: ", required=False)
                cid = cli_dao.criar_cliente({
                    "nome": nome, "cpf": cpf, "data_nascimento": data_nasc,
                    "endereco": end, "telefone": tel, "email": email
                })
                logger.info(f"cliente criado id={cid} cpf={cpf}")
                _audit(usuario, "criar", "cliente", cid, True)

            elif perfil == "admin" and op == "6":
                print("Tipos: 1-Automóvel  2-Residencial  3-Vida")
                t = ask("Tipo: ")
                titular = ask("Titular (nome): ")
                if t == "1":
                    modelo = ask("Modelo: ")
                    ano = int(ask("Ano: "))
                    placa = ask("Placa: ")
                    valor = float(ask("Valor do veículo: "))
                    sid = se_dao.criar_seguro_automovel(titular, valor, modelo, ano, placa)
                elif t == "2":
                    endereco_imovel = ask("Endereço do imóvel: ")
                    valor = float(ask("Valor do imóvel: "))
                    sid = se_dao.criar_seguro_residencial(titular, valor, endereco_imovel)
                elif t == "3":
                    valor = float(ask("Valor do seguro de vida: "))
                    beneficiarios = ask("Beneficiários (separados por vírgula): ")
                    sid = se_dao.criar_seguro_vida(titular, valor, beneficiarios)
                else:
                    print("Tipo inválido."); continue
                logger.info(f"seguro criado id={sid} titular={titular}")
                _audit(usuario, "criar", "seguro", sid, True)

            elif perfil == "admin" and op == "7":
                sid = int(ask("ID do seguro a emitir: "))
                numero = ap_dao.emitir_apolice(sid)
                if numero:
                    print(f"Apólice emitida Nº {numero}")
                    logger.info(f"apólice emitida numero={numero}")
                    _audit(usuario, "emitir", "apolice", numero, True)
                else:
                    print("Seguro inexistente.")
                    _audit(usuario, "emitir", "apolice", sid, False, "seguro inexistente")

            elif perfil == "admin" and op == "8":
                numero = buscar_por_numero_apolice()
                desc = ask("Descrição: ")
                data = ask("Data do sinistro (DD/MM/AAAA): ")
                sid = si_dao.registrar(numero, desc, data)
                if sid:
                    print(f"Sinistro registrado ID {sid}")
                    logger.info(f"sinistro registrado apolice={numero} id={sid}")
                    _audit(usuario, "registrar", "sinistro", sid, True)
                else:
                    print("Apólice inexistente/inalterável.")
                    _audit(usuario, "registrar", "sinistro", numero, False, "apólice inválida")

            elif perfil == "admin" and op == "9":
                cpf = buscar_por_cpf()
                tel = ask("Novo telefone: ", required=False)
                email = ask("Novo email: ", required=False)
                ok = cli_dao.atualizar_contato(cpf, tel, email)
                print("Atualizado." if ok else "Cliente não encontrado.")
                _audit(usuario, "editar", "cliente", cpf, bool(ok))

            elif perfil == "admin" and op == "10":
                numero = buscar_por_numero_apolice()
                if yesno(f"Confirmar cancelamento da apólice {numero}?"):
                    try:
                        if ap_dao.cancelar(numero):
                            print("Apólice cancelada.")
                            logger.info(f"apólice cancelada numero={numero}")
                            _audit(usuario, "cancelar", "apolice", numero, True)
                        else:
                            print("Não foi possível cancelar (inexistente).")
                            _audit(usuario, "cancelar", "apolice", numero, False)
                    except AppError as e:
                        print(e.user_message)
                        _audit(usuario, "cancelar", "apolice", numero, False, e.user_message)
                else:
                    print("Cancelamento abortado.")
                    _audit(usuario, "cancelar", "apolice", numero, False, "abortado pelo usuário")

            elif perfil == "admin" and op == "11":
                numero = buscar_por_numero_apolice()
                if si_dao.fechar(numero):
                    print("Sinistro fechado.")
                    logger.info(f"sinistro fechado apolice={numero}")
                    _audit(usuario, "fechar", "sinistro", numero, True)
                else:
                    print("Sinistro aberto não encontrado.")
                    _audit(usuario, "fechar", "sinistro", numero, False)

            elif perfil == "admin" and op == "13":
                cpf = buscar_por_cpf()
                print("Atenção: se houver apólices/seguros vinculados, a exclusão padrão será BLOQUEADA.")
                forcar = yesno("Deseja forçar exclusão em cascata (sinistros, apólices, seguros) antes do cliente?")
                if yesno(f"Confirmar exclusão do cliente {cpf}?"):
                    try:
                        ok = cli_dao.deletar_por_cpf(cpf, force=forcar)
                        if ok:
                            print("Cliente excluído.")
                            logger.info(f"cliente excluido cpf={cpf} force={forcar}")
                            _audit(usuario, "excluir", "cliente", cpf, True, f"force={forcar}")
                        else:
                            print("Cliente não encontrado.")
                            _audit(usuario, "excluir", "cliente", cpf, False, "não encontrado")
                    except AppError as e:
                        print(e.user_message)
                        logger.error(f"erro negocio excluir cliente cpf={cpf}: {e}")
                        _audit(usuario, "excluir", "cliente", cpf, False, e.user_message)
                    except Exception as e:
                        print("Erro ao excluir cliente.")
                        logger.exception(f"erro inesperado excluir cliente cpf={cpf}: {e}")
                        _audit(usuario, "excluir", "cliente", cpf, False, "erro inesperado")
                else:
                    print("Exclusão cancelada.")

            elif perfil == "admin" and op == "14":
                _cadastrar_usuario_cliente_flow(usuario)

            elif perfil == "admin" and op == "15":
                _listar_usuarios_flow(usuario)

            elif perfil == "admin" and op == "16":
                _editar_usuario_flow(usuario)

            elif perfil == "admin" and op == "17":
                _excluir_usuario_flow(usuario)

            elif perfil == "admin" and op == "18":
                sid = int(ask("ID do seguro a editar: "))
                campos = {}
                if yesno("Alterar titular?"): campos["titular"] = ask("Novo titular: ")
                if yesno("Alterar valor base?"): campos["valor_base"] = float(ask("Novo valor base: "))
                if yesno("Alterar modelo?"): campos["modelo"] = ask("Novo modelo: ", required=False)
                if yesno("Alterar ano?"): campos["ano"] = int(ask("Novo ano: "))
                if yesno("Alterar placa?"): campos["placa"] = ask("Nova placa: ", required=False)
                if yesno("Alterar endereço do imóvel?"): campos["endereco_imovel"] = ask("Novo endereço do imóvel: ", required=False)
                if yesno("Alterar beneficiários?"): campos["beneficiarios"] = ask("Novos beneficiários: ", required=False)
                ok = se_dao.editar_seguro(sid, **campos)
                print("Atualizado." if ok else "Seguro não encontrado ou nada a alterar.")
                _audit(usuario, "editar", "seguro", sid, bool(ok), f"campos={list(campos.keys())}")

            elif perfil == "admin" and op == "19":
                sid = int(ask("ID do seguro a excluir: "))
                if yesno(f"Confirmar exclusão do seguro {sid}?"):
                    try:
                        ok = se_dao.deletar_seguro(sid)
                        print("Seguro excluído." if ok else "Seguro não encontrado.")
                        _audit(usuario, "excluir", "seguro", sid, bool(ok))
                    except AppError as e:
                        print(e.user_message); _audit(usuario, "excluir", "seguro", sid, False, e.user_message)
                else:
                    print("Exclusão cancelada.")

            elif perfil == "admin" and op == "20":
                numero = buscar_por_numero_apolice()
                campos = {}
                if yesno("Alterar titular?"): campos["titular"] = ask("Novo titular: ")
                if yesno("Alterar valor mensal?"): campos["valor_mensal"] = float(ask("Novo valor mensal: "))
                ok = ap_dao.editar(numero, **campos)
                print("Atualizado." if ok else "Apólice não encontrada ou nada a alterar.")
                _audit(usuario, "editar", "apolice", numero, bool(ok), f"campos={list(campos.keys())}")

            elif perfil == "admin" and op == "21":
                sid = int(ask("ID do sinistro a editar: "))
                campos = {}
                if yesno("Alterar descrição?"): campos["descricao"] = ask("Nova descrição: ")
                if yesno("Alterar data?"): campos["data"] = ask("Nova data (DD/MM/AAAA): ")
                if yesno("Alterar status?"):
                    st = ask("Status (Aberto/Fechado): ")
                    campos["status"] = st
                try:
                    ok = si_dao.editar(sid, **campos)
                    print("Atualizado." if ok else "Sinistro não encontrado ou nada a alterar.")
                    _audit(usuario, "editar", "sinistro", sid, bool(ok), f"campos={list(campos.keys())}")
                except AppError as e:
                    print(e.user_message); _audit(usuario, "editar", "sinistro", sid, False, e.user_message)

            else:
                print("Opção inválida.")

        except OperacaoNaoPermitida as e:
            print(e.user_message); logger.error(f"bloqueado: {e}")
        except AppError as e:
            print(e.user_message); logger.error(f"erro de negócio: {e} | detalhes={getattr(e,'details',None)}")
        except Exception as e:
            print("Algo deu errado. Verifique os campos e tente novamente.")
            logger.exception(f"erro inesperado: {e}")
