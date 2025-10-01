from datetime import datetime

def validar_data_ddmmaa(s: str) -> bool:
    try:
        datetime.strptime(s, "%d/%m/%Y")
        return True
    except ValueError:
        return False

def limpar_cpf(cpf: str) -> str:
    return "".join(ch for ch in cpf if ch.isdigit())

def validar_cpf(cpf: str) -> bool:
    cpf = limpar_cpf(cpf)
    if len(cpf) != 11 or cpf == cpf[0]*11:
        return False
    soma1 = sum(int(cpf[i])*(10-i) for i in range(9))
    d1 = (soma1*10 % 11) % 10
    if d1 != int(cpf[9]):
        return False
    soma2 = sum(int(cpf[i])*(11-i) for i in range(10))
    d2 = (soma2*10 % 11) % 10
    return d2 == int(cpf[10])
