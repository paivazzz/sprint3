# app.py
from seguradora.db import init_db, get_conn
from seguradora.core.logging_conf import setup_logging
from seguradora.services.auth import autenticar, criar_usuario
from seguradora.cli.menu import loop_principal

def seed_admin():
    # cria admin padrão se não existir
    from seguradora.services.auth import _hash
    with get_conn() as conn:
        row = conn.execute("SELECT 1 FROM usuarios WHERE username='admin'").fetchone()
        if not row:
            criar_usuario("admin", "1234", "admin")

if __name__ == "__main__":
    setup_logging()
    init_db()
    seed_admin()

    print("=== LOGIN ===")
    user = input("Usuário: ").strip()
    pwd = input("Senha: ").strip()
    sessao = autenticar(user, pwd)
    if not sessao:
        print("Usuário ou senha inválidos.")
        raise SystemExit(1)

    print(f"Acesso liberado para {sessao['username']} ({sessao['perfil']})")
    loop_principal(sessao)
