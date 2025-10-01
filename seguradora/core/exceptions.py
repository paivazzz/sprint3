# seguradora/core/exceptions.py
class AppError(Exception):
    def __init__(self, message, user_message=None, details=None):
        super().__init__(message)
        self.user_message = user_message or "Operação não pôde ser concluída."
        self.details = details

class OperacaoNaoPermitida(AppError):
    def __init__(self, message="Operação não permitida para seu perfil."):
        super().__init__(message, user_message="Operação não permitida para seu perfil.")

class CpfInvalido(AppError):
    def __init__(self, cpf):
        super().__init__(f"CPF inválido: {cpf}", user_message="CPF inválido. Verifique e tente novamente.")

class ApoliceInexistente(AppError):
    def __init__(self, numero):
        super().__init__(f"Apólice inexistente: {numero}", user_message="Apólice não encontrada.")
