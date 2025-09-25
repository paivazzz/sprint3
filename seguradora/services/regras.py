# services/regras.py
from ..core.exceptions import RegraNegocio, ApoliceInexistente
from ..dao import apolices as ap_dao, sinistros as si_dao

def confirmar_cancelamento(numero: str, confirm: bool):
    if not confirm:
        raise RegraNegocio("Cancelamento abortado pelo usuário.")
    ap = ap_dao.obter_por_numero(numero)
    if not ap:
        raise ApoliceInexistente()
    if ap["status"] == "Cancelada":
        raise RegraNegocio("Apólice já está cancelada.")
    return True

def verificar_sinistro_fechamento(numero: str):
    ap = ap_dao.obter_por_numero(numero)
    if not ap:
        raise ApoliceInexistente()
    # fechamento será tentado; se não houver sinistro aberto, dao retorna False
    return True
