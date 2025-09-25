# core/exceptions.py
class AppError(Exception):
    user_message: str = "Ocorreu um erro."
    def __init__(self, user_message=None, *, details=None):
        super().__init__(user_message or self.user_message)
        self.details = details

class CpfInvalido(AppError):
    user_message = "CPF inválido."

class ApoliceInexistente(AppError):
    user_message = "Apólice não encontrada."

class OperacaoNaoPermitida(AppError):
    user_message = "Operação não permitida para seu perfil."

class RegraNegocio(AppError):
    user_message = "Operação não permitida pelas regras do sistema."
