from ..core.validators import limpar_cpf

def yesno(msg: str) -> bool:
    ans = input(f"{msg} [s/N]: ").strip().lower()
    return ans in ("s","sim","y","yes")

def ask(msg: str, required: bool = True) -> str:
    while True:
        x = input(msg).strip()
        if not required or x:
            return x
        print("Campo obrigatório.")

def buscar_por_cpf() -> str:
    cpf = input("CPF (somente números ou formatado): ").strip()
    return limpar_cpf(cpf)

def buscar_por_numero_apolice() -> str:
    return input("Número da apólice: ").strip()
