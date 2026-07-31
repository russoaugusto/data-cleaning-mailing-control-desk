import pandas as pd
import os

print("-> Iniciando PROCV inteligente por 'razao_social' (Chave Mestre)...")

pasta_data = r"C:\Users\AGS\Desktop\projeto-control-desk\data"
caminho_geral = os.path.join(pasta_data, "base_geral.csv")
caminho_higienizado = os.path.join(pasta_data, "mailing_rj_higienizado_pronto.csv")
caminho_salvar = os.path.join(pasta_data, "mailing_rj_higienizado_PERFEITO.csv")

print("-> Lendo tabelas originais...")
df_geral = pd.read_csv(caminho_geral, dtype=str, sep=';')
df_hig = pd.read_csv(caminho_higienizado, dtype=str, sep=';')

# 1. Isola apenas as colunas necessárias da base geral para não poluir o arquivo
df_geral_reduzido = df_geral[['razao_social', 'cnpj']].copy()
# Renomeia a coluna cnpj da base geral para não dar conflito no cruzamento
df_geral_reduzido.rename(columns={'cnpj': 'cnpj_verdadeiro'}, inplace=True)

# Remove duplicados da chave de cruzamento na base geral por segurança
df_geral_reduzido = df_geral_reduzido.drop_duplicates(subset=['razao_social'], keep='first')

print("-> Cruzando dados por Razão Social...")
# 🚀 O MERGE REAL: Faz o cruzamento trazendo apenas os registros que existem na tabela higienizada
df_resultado = pd.merge(df_hig, df_geral_reduzido, on='razao_social', how='left')

# Substitui a coluna 'cnpj' corrompida pela coluna do CNPJ verdadeiro recuperado
# Garante 14 dígitos completando com zeros à esquerda se faltar o caractere
df_resultado['cnpj'] = df_resultado['cnpj_verdadeiro'].str.strip().str.zfill(14)

# Remove a coluna auxiliar para deixar a tabela idêntica à original, mas corrigida
df_resultado.drop(columns=['cnpj_verdadeiro'], inplace=True)

# Salva o resultado perfeito na pasta /data
df_resultado.to_csv(caminho_salvar, sep=';', index=False, encoding='utf-8-sig')

print(f"===> [SUCESSO ABSOLUTO] Planilha gerada por PROCV: {os.path.basename(caminho_salvar)}")
print(f"-> Total de linhas geradas: {len(df_resultado)} (Bate certinho com o seu higienizado!)")
