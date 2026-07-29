import sqlite3
import os

def conectar_banco():
    # Trava o caminho absoluto na pasta raiz que você me mostrou no print
    caminho_banco = r"C:\Users\AGS\Desktop\projeto-control-desk\control_desk.db"
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
        cep TEXT,
        endereco_completo TEXT,
        tabulacao_3c TEXT DEFAULT NULL,
        agente_3c TEXT DEFAULT NULL,
        data_processamento TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_cnpj ON mailing_corporativo (cnpj)")
    conn.commit()
    conn.close()
