from seguradora.db import init_schema
from seguradora.core.logging_conf import setup_logging
from seguradora.services.auth import autenticar, criar_usuario
from seguradora.cli.menu import loop_principal

logger = setup_logging()

def seed_admin():
    """
    Cria admin padrão se ainda não existir.
    """
    try:
        criar_usuario("admin", "admin123", perfil="admin")
        logger.info("Admin criado: admin / admin123")
    except Exception:
        # Se já existe, seguimos
        pass

def main():
    init_schema()
    seed_admin()

    print("=== LOGIN ===")
    user = input("Usuário: ").strip()
    pwd = input("Senha: ").strip()
    try:
        sessao = autenticar(user, pwd)
        print(f"{sessao.get('username')} | Perfil: {sessao.get('perfil')} | Ativo")
        loop_principal(sessao)
    except Exception as e:
        # Mensagem amigável
        msg = getattr(e, "user_message", "Não foi possível autenticar.")
        print(msg)
        logger.exception(f"falha login: {e}")

if __name__ == "__main__":
    main()
