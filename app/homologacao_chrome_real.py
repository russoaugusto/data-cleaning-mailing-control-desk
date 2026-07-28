import pandas as pd
import time
import re
from playwright.sync_api import sync_playwright

def rodar_automacao_no_chrome_real():
    print("[INFO] Conectando no Google Chrome real que ja esta logado...")
    try:
        df = pd.read_csv("amostra_teste.csv", dtype=str, sep=';')
    except Exception as e:
        print(f"[ERRO] Falha ao ler amostra local: {e}")
        return

    with sync_playwright() as p:
        try:
            browser = p.chromium.connect_over_cdp("http://localhost:9222")
        except Exception as e:
            print(f"[ERRO CRÍTICO] O Chrome em modo de depuração não foi localizado: {e}")
            return
            
        default_context = browser.contexts[0]
        page = default_context.pages[0]
        
        print(f"[SUCESSO] Robô acoplado ao seu Chrome! URL Atual: {page.url}")
        print("[INFO] Iniciando esteira automatizada de consultas...")
        
        # Guarda a URL inicial de busca como nossa âncora de retorno
        url_busca_inicial = "https://consulta5.confirmeonline.com.br/siteconfirmeonline/faces/main.xhtml"
        novos_telefones = []
        
        for index, row in df.iterrows():
            cnpj = row.get('cnpj', row.iloc[0])
            print(f"\n[RASPAGEM] Processando registro {index + 1} - CNPJ: {cnpj}")
            
            try:
                # 🚀 AJUSTE CRÍTICO: Força o navegador a voltar para a tela inicial de busca a cada loop
                if page.url != url_busca_inicial:
                    print(" -> Retornando para a tela de filtros principal...")
                    page.goto(url_busca_inicial, wait_until="load")
                    time.sleep(2)
                
                # 1. Localiza a caixa de texto de CPF/CNPJ e clica para dar foco
                campo_cnpj = page.locator("input[type='text']").first
                campo_cnpj.click()
                
                # 2. Limpa o campo e digita o CNPJ como humano
                campo_cnpj.fill("")
                campo_cnpj.type(str(cnpj), delay=60)
                time.sleep(1)
                
                # 3. Dispara a busca pressionando ENTER no teclado
                print(" -> Pressionando ENTER para disparar a consulta...")
                campo_cnpj.press("Enter")
                
                # 4. Aguarda a ficha carregar na tela
                page.wait_for_timeout(4500)
                
                # 5. Captura o HTML interno e faz a mineração do telefone
                conteudo_pagina = page.content()
                
                # Procura por sequências numéricas de 10 ou 11 dígitos (DDD + Número) limpas
                padrao_tel = re.search(r'\b\d{2}\d{8,9}\b', re.sub(r'\D', '', conteudo_pagina))
                
                if padrao_tel:
                    tel_achado = padrao_tel.group(0)
                    print(f" -> [OK] Telefone capturado com sucesso: {tel_achado}")
                    novos_telefones.append(tel_achado)
                else:
                    # Varredura secundária caso o layout traga formatação de texto com traços
                    segunda_chance = re.search(r'\b\d{2}[- ]?\d{4,5}[- ]?\d{4}\b', conteudo_pagina)
                    if segunda_chance:
                        tel_achado = re.sub(r'\D', '', segunda_chance.group(0))
                        print(f" -> [OK] Telefone capturado na varredura secundária: {tel_achado}")
                        novos_telefones.append(tel_achado)
                    else:
                        print(" -> [AVISO] Nenhum telefone localizado na ficha deste CNPJ.")
                        novos_telefones.append("SEM_CONTATO")
                    
            except Exception as e:
                print(f" -> [FALHA] Erro de interface na linha {index}: {e}")
                novos_telefones.append("ERRO_INTERAÇÃO")
                
            # Intervalo de segurança para não sobrecarregar o servidor do Confirme Online
            time.sleep(2)
            
        # Grava os resultados de volta na planilha de teste
        df['telefone_homologado'] = novos_telefones
        df.to_csv("resultado_homologacao.csv", index=False, sep=';', encoding='utf-8-sig')
        print("\n[SUCESSO] Lote finalizado! Relatório 'resultado_homologacao.csv' gerado.")

if __name__ == "__main__":
    rodar_automacao_no_chrome_real()
