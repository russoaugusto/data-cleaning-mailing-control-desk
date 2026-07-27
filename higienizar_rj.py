import pandas as pd
import re
import requests
import time
from datetime import datetime

def limpar_e_formatar_telefone(tel_bruto):
    """Remove notação científica, limpa caracteres e padroniza o telefone."""
    if pd.isna(tel_bruto):
        return None
    
    tel_str = str(tel_bruto).strip()
    if 'E+' in tel_str or 'e+' in tel_str or 'E-' in tel_str:
        try:
            tel_str = str(int(float(tel_str.replace(',', '.'))))
        except:
            pass
            
    tel_numeros = re.sub(r'\D', '', tel_str)
    if len(tel_numeros) > 11 and tel_numeros.startswith('55'):
        tel_numeros = tel_numeros[2:]
    tel_numeros = tel_numeros.lstrip('0')
    
    if len(tel_numeros) >= 2 and tel_numeros[:2] in ['21', '22', '24']:
        if len(tel_numeros) in [10, 11] and len(set(tel_numeros)) > 1:
            return tel_numeros
    return None

def limpar_e_formatar_cnpj(cnpj_bruto):
    """Corrige notação científica do Excel e garante o CNPJ com 14 dígitos puros."""
    if pd.isna(cnpj_bruto):
        return ""
    
    cnpj_str = str(cnpj_bruto).strip()
    if 'E+' in cnpj_str or 'e+' in cnpj_str or 'E-' in cnpj_str or '-' in cnpj_str:
        try:
            cnpj_str = str(int(float(cnpj_str.replace(',', '.'))))
        except:
            pass
            
    cnpj_numeros = re.sub(r'\D', '', cnpj_str)
    if len(cnpj_numeros) > 0 and len(cnpj_numeros) < 14:
        cnpj_numeros = cnpj_numeros.zfill(14)
    return cnpj_numeros

def validar_regras_cnpj(cnpj):
    """Consulta a BrasilAPI com cabeçalho de segurança e controle de tráfego."""
    if not cnpj or len(cnpj) != 14:
        return "EXPURGAR_INVALIDO"
        
    url = f"https://brasilapi.com.br/api/cnpj/v1/{cnpj}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=7)
        
        if response.status_code == 200:
            dados = response.json()
            status = dados.get('descricao_situacao_cadastral', 'DESCONHECIDO').upper()
            
            if status in ['BAIXADA', 'INAPTA', 'SUSPENSA']:
                return "EXPURGAR_INATIVA"
                
            data_abertura_str = dados.get('data_abertura')
            if data_abertura_str:
                data_abertura = datetime.strptime(data_abertura_str, "%Y-%m-%d").date() if "-" in data_abertura_str else datetime.strptime(data_abertura_str, "%Y%m%d").date()
                data_atual = datetime.now().date()
                dias_ativa = (data_atual - data_abertura).days
                
                if dias_ativa < 180:
                    return "EXPURGAR_MENOS_6_MESES"
            return "APROVADO"
            
        elif response.status_code == 404:
            return "EXPURGAR_NAO_ENCONTRADO"
        elif response.status_code == 429:
            # Se a API pedir calma (limite excedido), espera 5 segundos e tenta o mesmo registro de novo
            time.sleep(5)
            return validar_regras_cnpj(cnpj)
        else:
            return f"EXPURGAR_HTTP_{response.status_code}"
            
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
        time.sleep(3)
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                return "APROVADO"
        except:
            pass
        return "EXPURGAR_OSCILACAO_REDE"

def processar_mailing_real(nome_arquivo_entrada):
    print("[INFO] Carregando a base bruta do cliente...")
    df = pd.read_csv(nome_arquivo_entrada, dtype=str, sep=None, engine='python')
    print(f"[LOG] Total de registros carregados: {len(df)}")
    
    coluna_cnpj = 'cnpj' if 'cnpj' in df.columns else df.columns
    coluna_tel = 'celular_1'

    print("[INFO] Padronizando e corrigindo strings de CNPJ...")
    df[coluna_cnpj] = df[coluna_cnpj].apply(limpar_e_formatar_cnpj)

    print("[INFO] Higienizando e aplicando regras geográficas de telefones (RJ)...")
    df['Telefone_Limpo'] = df[coluna_tel].apply(limpar_e_formatar_telefone)
    
    df_rj = df[df['Telefone_Limpo'].notna()].copy()
    print(f"[LOG] Registros remanescentes com DDDs válidos do RJ: {len(df_rj)}")
    
    total_antes_dedup = len(df_rj)
    df_rj.drop_duplicates(subset=['Telefone_Limpo'], keep='first', inplace=True)
    print(f"[LOG] Removidos {total_antes_dedup - len(df_rj)} números duplicados.")

    print("\n[MESA DE CONTROLE] Iniciando checagem total automatizada na Receita Federal (Status + Tempo de Mercado)...")
    
    resultado_regras = []
    total_leads = len(df_rj)
    print(f"[INFO] Processando a planilha inteira ({total_leads} registros). O robô rodará de forma contínua.")
    
    contador = 0
    for idx, row in df_rj.iterrows():
        cnpj_atual = row[coluna_cnpj]
        resultado = validar_regras_cnpj(cnpj_atual)
        resultado_regras.append(resultado)
        
        contador += 1
        # Imprime o progresso de 10 em 10 para o terminal não ficar poluído e travar por log
        if contador % 10 == 0 or contador == total_leads:
            print(f" -> Progresso: {contador}/{total_leads} leads avaliados... Último parecer: {resultado}")
            
        # Cadência de segurança sênior de 1.0s para estabilizar a fila da API de madrugada
        time.sleep(1.0)
        
    df_rj['parecer_controle'] = resultado_regras
    
    # Filtra e expurga os leads classificados como inativos ou novos
    total_antes_filtro = len(df_rj)
    df_final = df_rj[~df_rj['parecer_controle'].str.startswith('EXPURGAR')].copy()
    
    print(f"\n[LOG] Filtros de Inteligência Aplicados: Removidos {total_antes_filtro - len(df_final)} leads ociosos do mailing.")
    
    df_final[coluna_tel] = df_final['Telefone_Limpo']
    df_final.drop(columns=['Telefone_Limpo', 'parecer_controle'], inplace=True)
    
    nome_saida = "mailing_rj_higienizado_pronto.csv"
    df_final.to_csv(nome_saida, index=False, sep=';', encoding='utf-8-sig')
    print(f"\n[SUCESSO] Base de Elite gerada com êxito: '{nome_saida}' com {len(df_final)} registros!")

if __name__ == "__main__":
    pass
