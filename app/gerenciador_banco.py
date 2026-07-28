import sqlite3
import os

def conectar_banco():
    caminho_banco = os.path.join(os.getcwd(), "control_desk.db")
    return sqlite3.connect(caminho_banco, check_same_thread=False)

def inicializar_tabelas():
    conn = conectar_banco()
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS mailing_corporativo (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cnpj TEXT UNIQUE,
        nome_empresa TEXT,
        celular_original TEXT,
        operadora TEXT,
        status_receita TEXT DEFAULT 'PENDENTE',
        data_abertura TEXT,
        tempo_mercado_meses INTEGER,
        tabulacao_3c TEXT DEFAULT NULL,
        agente_3c TEXT DEFAULT NULL,
        data_processamento TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_cnpj ON mailing_corporativo (cnpj)")
    conn.commit()
    conn.close()

def salvar_lead_bruto(cnpj, nome, celular, operadora):
    conn = conectar_banco()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT OR IGNORE INTO mailing_corporativo (cnpj, nome_empresa, celular_original, operadora)
    VALUES (?, ?, ?, ?)
    """, (cnpj, nome, celular, operadora))
    conn.commit()
    conn.close()

def atualizar_tabulacao_discador(cnpj, status_ligacao, agente_responsavel):
    conn = conectar_banco()
    cursor = conn.cursor()
    cursor.execute("""
    UPDATE mailing_corporativo
    SET tabulacao_3c = ?, agente_3c = ?, data_processamento = CURRENT_TIMESTAMP
    WHERE cnpj = ?
    """, (status_ligacao, agente_responsavel, cnpj))
    conn.commit()
    conn.close()
