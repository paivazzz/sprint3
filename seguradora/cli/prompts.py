# cli/prompts.py
def yesno(msg: str) -> bool:
    while True:
        r = input(f"{msg} [s/N]: ").strip().lower()
        if r in ("s", "sim"):
            return True
        if r in ("n", "nao", "não", ""):
            return False

def ask(text: str, required=True):
    while True:
        v = input(text).strip()
        if v or not required:
            return v
        print("Campo obrigatório.")

def buscar_por_cpf() -> str:
    return input("CPF (somente números ou formatado): ").strip()

def buscar_por_numero_apolice() -> str:
    return input("Número da apólice: ").strip()

def buscar_por_nome() -> str:
    return input("Nome (ou parte): ").strip()
