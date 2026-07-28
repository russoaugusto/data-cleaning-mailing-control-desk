import sqlite3
import os

def conectar_banco():
    """Conecta ou cria o arquivo de banco de dados SQLite local."""
    caminho_banco = os.path.join(os.getcwd(), "control_desk.db")
    # O check_same_thread=False permite que o banco receba dados de múltiplas esteiras
    conn = sqlite3.connect(caminho_banco, check_same_thread=False)
    return conn

def inicializar_tabelas():
    """Cria a tabela de mailing estruturada se ela não existir no sistema."""
    conn = conectar_banco()
    cursor = conn.cursor()
    
    print("[BANCO] Inicializando infraestrutura de tabelas locais...")
    
    # Criamos uma tabela robusta que atende tanto o Robô 1 (Receita) quanto o Robô 2 (Credilink)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS mailing_corporativo (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cnpj TEXT UNIQUE,
        nome_empresa TEXT,
        celular_original TEXT,
        telefone_higienizado TEXT,
        operadora TEXT,
        status_receita TEXT DEFAULT 'PENDENTE',
        data_abertura TEXT,
        tempo_mercado_meses INTEGER,
        telefone_enriquecido_credilink TEXT DEFAULT NULL,
        data_processamento TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Criamos índices para que buscas por CNPJ e Telefone rodem em milissegundos
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_cnpj ON mailing_corporativo (cnpj)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tel_hig ON mailing_corporativo (telefone_higienizado)")
    
    conn.commit()
    conn.close()
    print("[BANCO] Tabelas e índices criados com sucesso e prontos para produção!")

def salvar_lead_bruto(cnpj, nome, celular, operadora):
    """Insere o lead bruto na esteira de processamento do banco (Ignora se já existir)."""
    conn = conectar_banco()
    cursor = conn.cursor()
    try:
        cursor.execute("""
        INSERT OR IGNORE INTO mailing_corporativo (cnpj, nome_empresa, celular_original, operadora)
        VALUES (?, ?, ?, ?)
        """, (cnpj, nome, celular, operadora))
        conn.commit()
    except Exception as e:
        print(f"[ERRO BANCO] Falha ao injetar lead {cnpj}: {e}")
    finally:
        conn.close()

def buscar_proximo_pendente_receita():
    """Busca o próximo CNPJ que precisa ser validado na API da Receita Federal."""
    conn = conectar_banco()
    cursor = conn.cursor()
    # Puxa o lead que ainda não passou pela checagem cronológica
    cursor.execute("""
    SELECT cnpj FROM mailing_corporativo 
    WHERE status_receita = 'PENDENTE' 
    LIMIT 1
    """)
    resultado = cursor.fetchone()
    conn.close()
    return resultado[0] if resultado else None

def atualizar_status_receita(cnpj, status, data_abertura, meses_ativa):
    """Atualiza as métricas cronológicas do CNPJ após a consulta externa."""
    conn = conectar_banco()
    cursor = conn.cursor()
    cursor.execute("""
    UPDATE mailing_corporativo
    SET status_receita = ?, data_abertura = ?, tempo_mercado_meses = ?
    WHERE cnpj = ?
    """, (status, data_abertura, meses_ativa, cnpj))
    conn.commit()
    conn.close()

def gravar_contato_credilink(cnpj, telefone_enriquecido):
    """Grava o número quente localizado na Credilink no registro do lead."""
    conn = conectar_banco()
    cursor = conn.cursor()
    cursor.execute("""
    UPDATE mailing_corporativo
    SET telefone_enriquecido_credilink = ?
    WHERE cnpj = ?
    """, (telefone_enriquecido, cnpj))
    conn.commit()
    conn.close()

if __name__ == "__main__":
    # Teste de inicialização local
    inicializar_tabelas()
