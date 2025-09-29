# seguradora/cli/menu.py
from ..core.exceptions import AppError, OperacaoNaoPermitida
from ..core.logging_conf import setup_logging
from ..services import relatorios
from ..dao import clientes as cli_dao, seguros as se_dao, apolices as ap_dao, sinistros as si_dao
from ..dao import auditoria as aud
from .prompts import yesno, ask, buscar_por_cpf, buscar_por_numero_apolice
from datetime import datetime
import shutil

logger = setup_logging()

def _audit(usuario, op, entidade, entidade_id, ok, detalhes=None):
    aud.registrar(usuario["username"], op, entidade, entidade_id, ok, detalhes)

def _guard(perfil_ativo, precisa_admin=False):
    if precisa_admin and perfil_ativo != "admin":
        raise OperacaoNaoPermitida()

def _print_menu_grid(perfil: str):
    """
    Imprime o menu em grade (4 colunas), mantendo a sequência:
    1,2,3,4,5,6,7,8,9,10,11,12,13,0 (se admin), senão só as opções permitidas.
    """
    itens = [
        "[1] Listar Clientes",
        "[2] Listar Seguros",
        "[3] Listar Apólices",
        "[4] Listar Sinistros",
    ]
    if perfil == "admin":
        itens += [
            "[5] Cadastrar Cliente",
            "[6] Cadastrar Seguro",
            "[7] Emitir Apólice",
            "[8] Registrar Sinistro",
            "[9] Editar Cliente",
            "[10] Cancelar Apólice",
            "[11] Fechar Sinistro",
        ]
    itens += ["[12] Relatórios"]
    if perfil == "admin":
        itens += ["[13] Excluir Cliente"]
    itens += ["[0] Sair"]

    cols = 4
    width = shutil.get_terminal_size().columns
    col_width = max(24, width // cols - 2)  # largura mínima para não quebrar
    print("\n=== MENU ===")
    for i, label in enumerate(itens):
        end = "\n" if (i % cols == cols - 1) else ""
        print(label.ljust(col_width), end=end)
    if len(itens) % cols != 0:
        print()  # quebra de linha final

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

        if sub == "1":
            rows = relatorios.receita_mensal_prevista(); last = rows
            for r in rows:
                valor = r['receita'] if r['receita'] is not None else 0
                print(f"{r['ym']}: R${valor:.2f}")
        elif sub == "2":
            rows = relatorios.top_clientes_por_valor_segurado(); last = rows
            for r in rows:
                print(f"{r['cliente']}: R${r['total']:.2f}")
        elif sub == "3":
            rows = relatorios.sinistros_por_status(); last = rows
            for r in rows:
                print(f"{r['status']}: {r['qtd']}")
        elif sub == "4":
            ini = input("De (YYYY-MM): ").strip()
            fim = input("Até (YYYY-MM): ").strip()
            rows = relatorios.sinistros_por_periodo(ini, fim); last = rows
            for r in rows:
                print(f"{r['ym']}: {r['qtd']} sinistro(s)")
        elif sub == "5":
            if last:
                caminho = relatorios.export_csv(f"rel_{datetime.now().strftime('%Y%m%d_%H%M%S')}", last)
                print(f"Exportado: {caminho}")
            else:
                print("Nada para exportar ainda. Gere um relatório primeiro.")
        elif sub == "0":
            break
        else:
            print("Opção inválida.")

def loop_principal(sessao):
    perfil = sessao["perfil"]
    usuario = {"username": sessao["username"], "perfil": perfil}

    while True:
        _print_menu_grid(perfil)
        op = input("Escolha uma opção: ").strip()
        try:
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
                        extra = f"{r['modelo']} {r['ano']} ({r['placa']})"
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
                    print(f"Apólice {s['apolice_numero']} | {s['data']} | {s['status']} | {s['descricao']}")

            elif op == "5":
                _guard(perfil, precisa_admin=True)
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

            elif op == "6":
                _guard(perfil, precisa_admin=True)
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

            elif op == "7":
                _guard(perfil, precisa_admin=True)
                sid = int(ask("ID do seguro a emitir: "))
                numero = ap_dao.emitir_apolice(sid)
                if numero:
                    print(f"Apólice emitida Nº {numero}")
                    logger.info(f"apólice emitida numero={numero}")
                    _audit(usuario, "emitir", "apolice", numero, True)
                else:
                    print("Seguro inexistente.")
                    _audit(usuario, "emitir", "apolice", sid, False, "seguro inexistente")

            elif op == "8":
                _guard(perfil, precisa_admin=True)
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

            elif op == "9":
                _guard(perfil, precisa_admin=True)
                cpf = buscar_por_cpf()
                tel = ask("Novo telefone: ", required=False)
                email = ask("Novo email: ", required=False)
                ok = cli_dao.atualizar_contato(cpf, tel, email)
                print("Atualizado." if ok else "Cliente não encontrado.")
                _audit(usuario, "editar", "cliente", cpf, bool(ok))

            elif op == "10":
                _guard(perfil, precisa_admin=True)
                numero = buscar_por_numero_apolice()
                if yesno(f"Confirmar cancelamento da apólice {numero}?"):
                    if ap_dao.cancelar(numero):
                        print("Apólice cancelada.")
                        logger.info(f"apólice cancelada numero={numero}")
                        _audit(usuario, "cancelar", "apolice", numero, True)
                    else:
                        print("Não foi possível cancelar (já cancelada ou inexistente).")
                        _audit(usuario, "cancelar", "apolice", numero, False)
                else:
                    print("Cancelamento abortado.")
                    _audit(usuario, "cancelar", "apolice", numero, False, "abortado pelo usuário")

            elif op == "11":
                _guard(perfil, precisa_admin=True)
                numero = buscar_por_numero_apolice()
                if si_dao.fechar(numero):
                    print("Sinistro fechado.")
                    logger.info(f"sinistro fechado apolice={numero}")
                    _audit(usuario, "fechar", "sinistro", numero, True)
                else:
                    print("Sinistro aberto não encontrado.")
                    _audit(usuario, "fechar", "sinistro", numero, False)

            elif op == "12":
                _submenu_relatorios()

            elif op == "13":
                _guard(perfil, precisa_admin=True)
                cpf = buscar_por_cpf()
                print("atenção: se houver apólices/seguros vinculados, a exclusão PADRÃO será BLOQUEADA.")
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

            elif op == "0":
                print("Encerrando...")
                break

            else:
                print("Opção inválida.")

        except OperacaoNaoPermitida as e:
            print(e.user_message); logger.error(f"bloqueado: {e}")
        except AppError as e:
            print(e.user_message); logger.error(f"erro de negócio: {e} | detalhes={getattr(e,'details',None)}")
        except Exception as e:
            print("Algo deu errado. Verifique os campos e tente novamente.")
            logger.exception(f"erro inesperado: {e}")
