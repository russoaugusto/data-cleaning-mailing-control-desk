import pandas as pd
import os

print("-> Iniciando extração do LOTE 2 (20.000 leads inéditos) para a 3C Plus...")

# Caminho da sua planilha que já foi corrigida e cruzada com os CNPJs certos
caminho = r"C:\Users\AGS\Desktop\projeto-control-desk\data\mailing_rj_higienizado_PERFEITO.csv"

if not os.path.exists(caminho):
    caminho = "mailing_rj_higienizado_PERFEITO.csv"

# Lê a planilha com os dados restaurados
df = pd.read_csv(caminho, dtype=str, sep=';')

df_out = pd.DataFrame()

# 1. Mapeia Nome por Extenso
df_out['Nome'] = df['razao_social'].str.strip() if 'razao_social' in df.columns else df[df.columns].str.strip()

# 2. Mapeia Telefone limpo (Coluna 'celular_1')
df_out['Telefone'] = df['celular_1'].str.strip() if 'celular_1' in df.columns else df['celular_1_'].str.strip()

# 3. Mapeia o CNPJ de 14 dígitos que recuperamos da base geral
cnpj_limpo = df['cnpj'].str.strip().str.zfill(14)
df_out['CNPJ_Tratado'] = cnpj_limpo.str.slice(0,2) + '.' + cnpj_limpo.str.slice(2,5) + '.' + cnpj_limpo.str.slice(5,8) + '/' + cnpj_limpo.str.slice(8,12) + '-' + cnpj_limpo.str.slice(12,14)

# 4. Mapeia a Operadora da última coluna (Coluna AG)
df_out['Operadora_Atual'] = df.iloc[:, -1].str.strip().str.upper()

# 5. Mapeia CEP e Endereço Completo
df_out['CEP'] = df['cep'].str.strip() if 'cep' in df.columns else '00000-000'

logr = df['logradouro'] if 'logradouro' in df.columns else ''
num = df['numero'] if 'numero' in df.columns else ''
bairro = df['bairro'] if 'bairro' in df.columns else ''
cidade = df['municipio'] if 'municipio' in df.columns else ''
df_out['Endereco_Completo'] = logr + ', ' + num + ' - ' + bairro + ', ' + cidade + '/RJ'

# 🚀 O PULO DO GATO: Ignora as primeiras 10.000 linhas e extrai as próximas 20.000 (linhas 10.000 até 30.000)
df_20k = df_out.iloc[10000:30000]

print("\n================ RETORNO DO MAILING (5 LEADS DE TESTE DO NOVO LOTE) ================")
for idx, row in df_20k.head(5).iterrows():
    print(f"Lead {idx+1}: {row['Nome'][:25]} | Tel: {row['Telefone']} | CNPJ: {row['CNPJ_Tratado']} | OPERADORA: {row['Operadora_Atual']}")
print("====================================================================================\n")

# Gera o novo arquivo fatiado pronto para a nova lista
try:
    df_20k.to_csv('LOTE_2_20K_RJ_3C_PLUS.csv', sep=';', index=False, encoding='utf-8-sig')
    print("===> [SUCESSO TOTAL] ARQUIVO 'LOTE_2_20K_RJ_3C_PLUS.csv' GERADO NA PASTA DO PROJETO!")
except Exception as e:
    print(f"[AVISO CRÍTICO] Feche as planilhas no Excel para o Windows permitir gravar o arquivo! Erro: {e}")
