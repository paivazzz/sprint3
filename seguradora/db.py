# seguradora/db.py
import os
import sqlite3

DB_PATH = os.environ.get("SEGU_DB", "seguradora.db")

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    # Cascatas são controladas via DAO (mantenha OFF aqui para evitar efeitos colaterais)
    conn.execute("PRAGMA foreign_keys=OFF")
    return conn

def init_schema():
    with get_conn() as conn:
        conn.executescript("""
        -- =========================
        -- CLIENTES
        -- =========================
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            cpf TEXT NOT NULL UNIQUE,
            data_nascimento TEXT NOT NULL, -- DD/MM/AAAA
            endereco TEXT,
            telefone TEXT,
            email TEXT,
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- =========================
        -- SEGUROS
        -- =========================
        CREATE TABLE IF NOT EXISTS seguros (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo TEXT NOT NULL CHECK(tipo IN ('Automóvel','Residencial','Vida')),
            titular TEXT NOT NULL,           -- nome do cliente (display)
            valor_base REAL NOT NULL,

            -- específicos
            modelo TEXT,
            ano INTEGER,
            placa TEXT,           -- Automóvel
            endereco_imovel TEXT, -- Residencial
            beneficiarios TEXT,   -- Vida

            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- =========================
        -- APÓLICES
        -- =========================
        CREATE TABLE IF NOT EXISTS apolices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero TEXT NOT NULL UNIQUE,
            seguro_id INTEGER NOT NULL,
            tipo TEXT NOT NULL,
            titular TEXT NOT NULL,
            valor_mensal REAL NOT NULL,
            status TEXT NOT NULL CHECK(status IN ('Ativa','Cancelada')),
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- =========================
        -- SINISTROS
        -- =========================
        CREATE TABLE IF NOT EXISTS sinistros (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            apolice_numero TEXT NOT NULL,
            descricao TEXT NOT NULL,
            data TEXT NOT NULL,   -- DD/MM/AAAA
            status TEXT NOT NULL CHECK(status IN ('Aberto','Fechado')) DEFAULT 'Aberto',
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- =========================
        -- AUDITORIA
        -- =========================
        CREATE TABLE IF NOT EXISTS auditoria (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            username TEXT NOT NULL,
            operacao TEXT NOT NULL,
            entidade TEXT NOT NULL,
            entidade_id TEXT,
            ok INTEGER NOT NULL,          -- 1=ok, 0=erro
            detalhes TEXT
        );

        -- =========================
        -- USUÁRIOS (AUTENTICAÇÃO)
        -- =========================
        -- Importante: o services/auth.py espera PRIMARY KEY em 'username'
        CREATE TABLE IF NOT EXISTS usuarios (
            username    TEXT PRIMARY KEY,
            senha_hash  TEXT NOT NULL,
            perfil      TEXT NOT NULL CHECK (perfil IN ('admin','comum','cliente')),
            cliente_cpf TEXT,                               -- se perfil='cliente', vincula a clientes.cpf
            ativo       INTEGER NOT NULL DEFAULT 1,         -- 1=ativo, 0=inativo
            criado_em   TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        -- =========================
        -- ÍNDICES
        -- =========================
        CREATE INDEX IF NOT EXISTS idx_apolices_status   ON apolices(status);
        CREATE INDEX IF NOT EXISTS idx_sinistros_status  ON sinistros(status);
        CREATE INDEX IF NOT EXISTS idx_sinistros_apolice ON sinistros(apolice_numero);
        CREATE INDEX IF NOT EXISTS idx_usuarios_perfil   ON usuarios(perfil);
        """)
