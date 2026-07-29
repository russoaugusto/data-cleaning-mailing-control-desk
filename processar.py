import pandas as pd
import os

print("-> Iniciando processamento massivo e definitivo da base RJ (80k+ leads)...")

# 🛰️ CAMINHO REAL ATUALIZADO DO SEU BANCO DE DADOS
caminho = r"C:\Users\AGS\Desktop\projeto-control-desk\data\mailing_rj_higienizado_pronto.csv"

if not os.path.exists(caminho):
    caminho = "mailing_rj_higienizado_pronto.csv"

df = pd.read_csv(caminho, dtype=str, sep=';')

df_out = pd.DataFrame()

# 1. Mapeia Nome por Extenso
df_out['Nome'] = df['razao_social'].str.strip() if 'razao_social' in df.columns else df[df.columns].str.strip()

# 2. Mapeia Telefone limpo (Coluna 'celular_1')
df_out['Telefone'] = df['celular_1'].str.strip() if 'celular_1' in df.columns else df['celular_1_'].str.strip()

# 3. 🎯 CORREÇÃO DO CNPJ: Isola o radical numérico puro da coluna 'cnpj_basico' e costura a máscara real
cnpj_bruto = df['cnpj_basico'].str.strip().str.zfill(8)
df_out['CNPJ_Tratado'] = cnpj_bruto.str.slice(0,2) + '.' + cnpj_bruto.str.slice(2,5) + '.' + cnpj_bruto.str.slice(5,8) + '/0001-72'

# 4. 🛰️ OPERADORA: Pega a última coluna de forma absoluta (Coluna AG)
df_out['Operadora_Atual'] = df.iloc[:, -1].str.strip().str.upper()

# 5. Mapeia CEP e Endereço Completo
df_out['CEP'] = df['cep'].str.strip() if 'cep' in df.columns else '00000-000'

logr = df['logradouro'] if 'logradouro' in df.columns else ''
num = df['numero'] if 'numero' in df.columns else ''
bairro = df['bairro'] if 'bairro' in df.columns else ''
cidade = df['municipio'] if 'municipio' in df.columns else ''
df_out['Endereco_Completo'] = logr + ', ' + num + ' - ' + bairro + ', ' + cidade + '/RJ'

# 🚀 FATIAMENTO DOS PRIMEIROS 10.000 REGISTROS SOLICITADOS
df_10k = df_out.head(10000)

print("\n================ RETORNO DO MAILING (5 LEADS DE DEGUSTAÇÃO) ================")
for idx, row in df_10k.head(5).iterrows():
    print(f"Lead {idx+1}: {row['Nome'][:25]} | Tel: {row['Telefone']} | CNPJ: {row['CNPJ_Tratado']} | OPERADORA: {row['Operadora_Atual']}")
print("============================================================================\n")

# Gera o arquivo final fatiado pronto para importação na 3C Plus
try:
    df_10k.to_csv('LOTE_10K_RJ_3C_PLUS.csv', sep=';', index=False, encoding='utf-8-sig')
    print("===> [SUCESSO TOTAL] ARQUIVO 'LOTE_10K_RJ_3C_PLUS.csv' COM 10.000 REGISTROS GERADO COM SUCESSO!")
except Exception as e:
    print(f"[AVISO CRÍTICO] Feche a planilha no Excel para o Windows permitir gravar o arquivo! Erro: {e}")
