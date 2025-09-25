# db.py
import sqlite3
from pathlib import Path

DB_PATH = Path("seguradora.sqlite3")

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

SCHEMA_SQL = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS usuarios (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT UNIQUE NOT NULL,
  senha_hash TEXT NOT NULL,
  perfil TEXT NOT NULL CHECK (perfil IN ('admin','comum')),
  criado_em TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS clientes (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  nome TEXT NOT NULL,
  cpf TEXT UNIQUE NOT NULL,
  data_nascimento TEXT NOT NULL,
  endereco TEXT,
  telefone TEXT,
  email TEXT,
  criado_em TEXT NOT NULL,
  atualizado_em TEXT
);

-- seguros: vamos usar um tipo + colunas específicas opcionais
CREATE TABLE IF NOT EXISTS seguros (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  titular TEXT NOT NULL,          -- nome do cliente (compatível com sprint 2)
  tipo TEXT NOT NULL CHECK (tipo IN ('Automóvel','Residencial','Vida')),
  valor_base REAL NOT NULL,
  modelo TEXT, ano INTEGER, placa TEXT,          -- automóvel
  endereco_imovel TEXT,                           -- residencial
  beneficiarios TEXT,                             -- vida (CSV)
  criado_em TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS apolices (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  numero TEXT UNIQUE NOT NULL,
  seguro_id INTEGER NOT NULL REFERENCES seguros(id) ON DELETE CASCADE,
  valor_mensal REAL NOT NULL,
  status TEXT NOT NULL DEFAULT 'Ativa' CHECK (status IN ('Ativa','Cancelada')),
  criado_em TEXT NOT NULL,
  cancelado_em TEXT
);

CREATE TABLE IF NOT EXISTS sinistros (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  apolice_id INTEGER NOT NULL REFERENCES apolices(id) ON DELETE CASCADE,
  descricao TEXT NOT NULL,
  data TEXT NOT NULL,
  status TEXT NOT NULL CHECK (status IN ('Aberto','Fechado')),
  criado_em TEXT NOT NULL,
  fechado_em TEXT
);

-- auditoria
CREATE TABLE IF NOT EXISTS auditoria (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  timestamp TEXT NOT NULL,
  usuario TEXT NOT NULL,
  operacao TEXT NOT NULL,
  entidade TEXT NOT NULL,           -- 'cliente','apolice','sinistro','seguro','usuario'
  entidade_id TEXT,                 -- id ou numero
  sucesso INTEGER NOT NULL,         -- 0/1
  detalhes TEXT
);

-- índices úteis
CREATE INDEX IF NOT EXISTS idx_clientes_cpf ON clientes(cpf);
CREATE INDEX IF NOT EXISTS idx_apolices_numero ON apolices(numero);
CREATE INDEX IF NOT EXISTS idx_sinistros_status ON sinistros(status);
"""

def init_db():
    with get_conn() as conn:
        conn.executescript(SCHEMA_SQL)
