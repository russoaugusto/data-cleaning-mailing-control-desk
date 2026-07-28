import pandas as pd
import time
import re
from playwright.sync_api import sync_playwright

# ==============================================================================
# INSIRA ABAIXO O VALOR DO COOKIE JSESSIONID QUE VOCÊ COPIOU DO SEU CHROME
# ==============================================================================
COOKIE_JSESSIONID = "2506893EE174FFE6752959563DB47250"
# ==============================================================================

def rodar_raspagem_direta():
    print("[INFO] Iniciando esteira sênior via Injeção de Sessão Corrigida...")
    try:
        df = pd.read_csv("amostra_teste.csv", dtype=str, sep=';')
    except Exception as e:
        print(f"[ERRO] Falha ao ler amostra local: {e}")
        return

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=300)
        context = browser.new_context()
        page = context.new_page()
        
        # Desativa o timeout de navegação para a rede lentas ou oscilações de banco de dados
        page.set_default_navigation_timeout(0)
        page.set_default_timeout(0)
        
        print("[ROBÔ] Aplicando engenharia de cookies no domínio Confirme Online...")
        # LÓGICA SÊNIOR AMARRADA: Injeta o cookie cobrindo as duas rotas principais para o servidor aceitar
        context.add_cookies([
            {
                "name": "JSESSIONID",
                "value": COOKIE_JSESSIONID,
                "domain": "consulta5.confirmeonline.com.br",
                "path": "/"
            },
            {
                "name": "JSESSIONID",
                "value": COOKIE_JSESSIONID,
                "domain": "consulta5.confirmeonline.com.br",
                "path": "/siteconfirmeonline"
            }
        ])
        
        # Navega diretamente para a URL interna que você descobriu na última foto
        url_interna = "https://consulta5.confirmeonline.com.br/siteconfirmeonline/faces/main.xhtml"
        print(f"[ROBÔ] Forçando acesso direto à URL do painel: {url_interna}")
        page.goto(url_interna, wait_until="networkidle")
        time.sleep(30) # Pausa estratégica para a sessão fixar no servidor deles

        novos_telefones = []
        print("\n[INFO] Iniciando esteira automática de mineração de leads...")
        
        for index, row in df.iterrows():
            cnpj = row.get('cnpj', row.iloc[0])
            print(f"\n[RASPAGEM] Consultando CNPJ: {cnpj}")
            
            try:
                # Retorna para a página principal de busca para limpar consultas anteriores
                if page.url != url_interna:
                    page.goto(url_interna, wait_until="networkidle")
                
                # Procura a caixa de texto de CPF/CNPJ e clica antes de digitar para focar
                campo_cnpj = page.locator("input[type='text']").first
                campo_cnpj.click()
                campo_cnpj.fill("") # Limpa consulta anterior
                campo_cnpj.fill(str(cnpj))
                
                # Localiza e clica no botão de pesquisar/buscar da tela interna
                # Mapeia inputs do tipo submit ou botões vermelhos ativos
                botao_busca = page.locator("input[type='submit'], button, input[value*='Pesquisar']").first
                botao_busca.click()
                
                # Aguarda o processamento do painel
                page.wait_for_timeout(4000)
                
                # Captura todo o texto da página interna da ficha para minerar o telefone
                conteudo_pagina = page.content()
                
                # Regex estruturada para capturar padrões de telefones móveis ou fixos (DDD de 2 dígitos + número)
                padrao_tel = re.search(r'\b\d{2}\d{8,9}\b', re.sub(r'\D', '', conteudo_pagina))
                
                if padrao_tel:
                    tel_achado = padrao_tel.group(0)
                    print(f" -> [OK] Telefone minerado na ficha com sucesso: {tel_achado}")
                    novos_telefones.append(tel_achado)
                else:
                    # Faz uma varredura secundária procurando texto corrido caso o layout mude
                    segunda_chance = re.search(r'\b\d{2}[- ]?\d{4,5}[- ]?\d{4}\b', conteudo_pagina)
                    if segunda_chance:
                        tel_achado = re.sub(r'\D', '', segunda_chance.group(0))
                        print(f" -> [OK] Telefone capturado em varredura secundária: {tel_achado}")
                        novos_telefones.append(tel_achado)
                    else:
                        print(" -> [AVISO] CNPJ consultado, mas nenhum contato telefônico foi listado.")
                        novos_telefones.append("SEM_CONTATO")
                    
            except Exception as e:
                print(f" -> [FALHA] Erro de interface na linha {index}: {e}")
                novos_telefones.append("ERRO_INTERAÇÃO")
                
            time.sleep(2)
            
        print("\n[INFO] Finalizando rotina técnica e fechando navegador...")
        browser.close()
        
        df['telefone_homologado'] = novos_telefones
        df.to_csv("resultado_homologacao.csv", index=False, sep=';', encoding='utf-8-sig')
        print("[SUCESSO] Relatório de homologação 'resultado_homologacao.csv' gerado na pasta!")

if __name__ == "__main__":
    rodar_raspagem_direta()
