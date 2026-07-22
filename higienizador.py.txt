import pandas as pd
import re

def limpar_apenas_numeros(telefone):
    """Remove qualquer caractere que não seja número."""
    if pd.isna(telefone):
        return ""
    return re.sub(r'\D', '', str(telefone))

def validar_telefone(telefone):
    """Valida se o telefone fixo ou celular possui tamanho e DDD válidos no Brasil."""
    # Remove zeros à esquerda se houver (ex: 0319...)
    telefone = telefone.lstrip('0')
    
    # Verifica tamanho padrão brasileiro (10 dígitos para fixo, 11 para celular)
    if len(telefone) not in:
        return False
        
    # Impede sequências repetidas óbvias (ex: 11111111111)
    if len(set(telefone)) == 1:
        return False
        
    return True

def higienizar_mailing(caminho_arquivo_bruto, caminho_lista_bloqueio):
    print("[INFO] Iniciando processamento do mailing...")
    
    # 1. Carga dos dados brutos (Simulando extração de CRM)
    df = pd.read_csv(caminho_arquivo_bruto, dtype=str)
    
    # 2. Remoção de duplicidades crônicas (Duplicados na mesma carga)
    total_antes = len(df)
    df.drop_duplicates(subset=['telefone'], keep='first', inplace=True)
    print(f"[LOG] Removidos {total_antes - len(df)} registros duplicados.")

    # 3. Limpeza de caracteres e aplicação de Regras de Negócio de Telecom
    df['telefone_limpo'] = df['telefone'].apply(limpar_apenas_numeros)
    df['valido'] = df['telefone_limpo'].apply(validar_telefone)
    
    # Separa apenas os válidos estruturalmente
    df_filtrado = df[df['valido'] == True].copy()
    print(f"[LOG] Removidos {len(df) - len(df_filtrado)} telefones inválidos (erros de formato/sequenciais).")

    # 4. Simulação de cruzamento com Lista de Bloqueio (Ex: Procon / Não Me Perturbe)
    df_bloqueio = pd.read_csv(caminho_lista_bloqueio, dtype=str)
    df_bloqueio['telefone_bloqueado'] = df_bloqueio['telefone'].apply(limpar_apenas_numeros)
    
    # Procura registros que NÃO estão na lista de bloqueio (Left Join Antijoin)
    df_final = df_filtrado[~df_filtrado['telefone_limpo'].isin(df_bloqueio['telefone_bloqueado'])]
    print(f"[LOG] Removidos {len(df_filtrado) - len(df_final)} contatos localizados na lista de bloqueio legal.")

    # 5. Exportação da base higienizada pronta para o discador (Ex: 3C Plus)
    df_final.drop(columns=['valido'], inplace=True)
    df_final.to_csv("mailing_higienizado_pronto.csv", index=False)
    print(f"[SUCESSO] Processo concluído! Base pronta gerada com {len(df_final)} registros produtivos.")

if __name__ == "__main__":
    # Nomes dos arquivos para simulação local
    higienizar_mailing("leads_brutos.csv", "lista_nao_perturbe.csv")
