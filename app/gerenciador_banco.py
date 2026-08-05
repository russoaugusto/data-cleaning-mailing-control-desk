import sqlite3
import os

# Caminho do banco. Mantém o caminho fixo que você já usa, mas cai para uma
# pasta local (ao lado deste arquivo) se aquele caminho não existir na máquina
# que rodar o programa - evita quebrar em outro PC/pasta.
CAMINHO_FIXO = r"C:\Users\AGS\Desktop\projeto-control-desk\control_desk.db"


def _resolver_caminho_banco():
    pasta_fixa = os.path.dirname(CAMINHO_FIXO)
    if os.path.isdir(pasta_fixa):
        return CAMINHO_FIXO
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "control_desk.db")


def conectar_banco():
    return sqlite3.connect(_resolver_caminho_banco(), check_same_thread=False)


def _colunas_existentes(cursor, tabela):
    cursor.execute(f"PRAGMA table_info({tabela})")
    return {linha[1] for linha in cursor.fetchall()}


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

    # Migração incremental: adiciona colunas novas em bancos já existentes
    # sem apagar nada que já foi carregado.
    colunas = _colunas_existentes(cursor, "mailing_corporativo")
    migracoes = {
        "status_envio_3c": "TEXT DEFAULT 'pendente'",
        "id_lista_3c": "TEXT DEFAULT NULL",
        "id_campanha_3c": "TEXT DEFAULT NULL",
        "data_envio_3c": "TIMESTAMP DEFAULT NULL",
        "data_ultima_tabulacao": "TIMESTAMP DEFAULT NULL",
        "call_id_3c": "TEXT DEFAULT NULL",
    }
    for coluna, definicao in migracoes.items():
        if coluna not in colunas:
            cursor.execute(f"ALTER TABLE mailing_corporativo ADD COLUMN {coluna} {definicao}")

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_status_envio ON mailing_corporativo (status_envio_3c)")
    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# LEADS: ENVIO PARA 3C (novos leads / evitar duplicidade em listas existentes)
# ---------------------------------------------------------------------------

def buscar_leads_pendentes(limite):
    """Retorna leads que ainda não foram enviados a NENHUMA lista da 3C."""
    conn = conectar_banco()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT cnpj, nome_empresa, celular_original, operadora, cep, endereco_completo
        FROM mailing_corporativo
        WHERE status_envio_3c IS NULL OR status_envio_3c = 'pendente'
        LIMIT ?
    """, (int(limite),))
    linhas = cursor.fetchall()
    conn.close()
    return linhas


def marcar_leads_enviados(cnpjs, id_lista, id_campanha):
    """Marca os leads como enviados, associando à lista/campanha usada.
    Isso é o que garante que, numa próxima importação ou num novo lote,
    o mesmo CNPJ não seja reenviado para a mesma esteira."""
    if not cnpjs:
        return
    conn = conectar_banco()
    cursor = conn.cursor()
    placeholders = ",".join("?" for _ in cnpjs)
    cursor.execute(f"""
        UPDATE mailing_corporativo
        SET status_envio_3c = 'enviado',
            id_lista_3c = ?,
            id_campanha_3c = ?,
            data_envio_3c = CURRENT_TIMESTAMP
        WHERE cnpj IN ({placeholders})
    """, [id_lista, id_campanha, *cnpjs])
    conn.commit()
    conn.close()


def contar_leads_por_status():
    conn = conectar_banco()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COALESCE(status_envio_3c, 'pendente'), COUNT(*)
        FROM mailing_corporativo
        GROUP BY 1
    """)
    resultado = dict(cursor.fetchall())
    conn.close()
    return resultado


# ---------------------------------------------------------------------------
# TABULAÇÕES: histórico de ligações vindo da 3C
# ---------------------------------------------------------------------------

def atualizar_tabulacao(cnpj, tabulacao, agente, call_id=None):
    conn = conectar_banco()
    cursor = conn.cursor()
    cnpj_limpo = str(cnpj).strip().zfill(14)
    cursor.execute("""
        UPDATE mailing_corporativo
        SET tabulacao_3c = ?,
            agente_3c = ?,
            call_id_3c = COALESCE(?, call_id_3c),
            data_ultima_tabulacao = CURRENT_TIMESTAMP
        WHERE cnpj = ?
    """, (tabulacao, agente, call_id, cnpj_limpo))
    linhas_afetadas = cursor.rowcount
    conn.commit()
    conn.close()
    return linhas_afetadas > 0


def contar_tabulacoes():
    conn = conectar_banco()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COALESCE(tabulacao_3c, 'SEM TABULAÇÃO'), COUNT(*)
        FROM mailing_corporativo
        GROUP BY 1
        ORDER BY 2 DESC
    """)
    resultado = cursor.fetchall()
    conn.close()
    return resultado
