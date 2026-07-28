import time
import requests
import re
from datetime import datetime
from playwright.sync_api import sync_playwright
import gerenciador_banco

def executar_esteira_receita(interface):
    interface.escrever_log("[ESTEIRA 1] Varrendo registros pendentes no Banco SQL...")
    
    while True:
        registro = gerenciador_banco.buscar_proximo_pendente_receita()
        if not registro:
            interface.escrever_log("[ESTEIRA 1] Concluído! Não existem mais CNPJs pendentes.")
            interface.atualizar_dashboard()
            break
            
        cnpj = registro[0]
        url = f"https://brasilapi.com.br{cnpj}"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        
        try:
            response = requests.get(url, headers=headers, timeout=5)
            if response.status_code == 200:
                dados = response.json()
                status = dados.get('descricao_situacao_cadastral', 'DESCONHECIDO').upper()
                
                if status in ['BAIXADA', 'INAPTA', 'SUSPENSA']:
                    parecer = "EXPURGAR_INATIVA"
                    gerenciador_banco.atualizar_status_receita(cnpj, parecer, "", 0)
                else:
                    data_abertura_str = dados.get('data_abertura')
                    if data_abertura_str:
                        dt = datetime.strptime(data_abertura_str, "%Y-%m-%d").date() if "-" in data_abertura_str else datetime.strptime(data_abertura_str, "%Y%m%d").date()
                        dias = (datetime.now().date() - dt).days
                        
                        if dias < 180:
                            parecer = "EXPURGAR_MENOS_6_MESES"
                            gerenciador_banco.atualizar_status_receita(cnpj, parecer, data_abertura_str, int(dias/30))
                        else:
                            parecer = "APROVADO"
                            gerenciador_banco.atualizar_status_receita(cnpj, parecer, data_abertura_str, int(dias/30))
                    else:
                        parecer = "APROVADO"
                        gerenciador_banco.atualizar_status_receita(cnpj, parecer, "", 0)
                        
                interface.escrever_log(f"CNPJ: {cnpj} | Parecer: {parecer}")
                interface.atualizar_dashboard()
            elif response.status_code == 429:
                interface.escrever_log("[AVISO] Servidor cheio. Recuando por 5 segundos...")
                time.sleep(5)
                continue
            else:
                gerenciador_banco.atualizar_status_receita(cnpj, f"EXPURGAR_HTTP_{response.status_code}", "", 0)
                interface.atualizar_dashboard()
        except Exception as e:
            interface.escrever_log(f"Oscilação de rede no CNPJ {cnpj}. Re-tentando...")
            time.sleep(2)
            continue
            
        time.sleep(1.2)

def executar_esteira_credilink(interface, token_api=None):
    if token_api:
        interface.escrever_log("[ESTEIRA 2] MODO API ATIVADO! Conectando via WebService...")
        interface.escrever_log("[INFO] Aguardando liberação das credenciais de produção pela Credilink.")
        return

    interface.escrever_log("[ESTEIRA 2] Buscando leads aprovados no banco local...")
    conn = gerenciador_banco.conectar_banco()
    cursor = conn.cursor()
    cursor.execute("SELECT cnpj FROM mailing_corporativo WHERE status_receita = 'APROVADO' AND telefone_enriquecido_credilink IS NULL")
    leads_aprovados = cursor.fetchall()
    conn.close()
    
    if not leads_aprovados:
        interface.escrever_log("[ESTEIRA 2] Sem registros pendentes de enriquecimento.")
        return

    interface.escrever_log(f"[ESTEIRA 2] Conectando ao Chrome na porta 9222 para minerar {len(leads_aprovados)} leads...")
    url_busca_inicial = "https://confirmeonline.com.br"

    with sync_playwright() as p:
        try:
            browser = p.chromium.connect_over_cdp("http://localhost:9222")
        except Exception as e:
            interface.escrever_log(f"[ERRO] Abra o Chrome no modo debug: {e}")
            return
            
        page = browser.contexts[0].pages[0]
        
        for item in leads_aprovados:
            cnpj = item[0]
            interface.escrever_log(f"[CREDILINK] Consultando CNPJ: {cnpj}...")
            
            try:
                if page.url != url_busca_inicial:
                    page.goto(url_busca_inicial, wait_until="load")
                    time.sleep(1.5)
                    
                campo_cnpj = page.locator("input[type='text']").first
                campo_cnpj.click()
                campo_cnpj.fill("")
                campo_cnpj.type(str(cnpj), delay=50)
                time.sleep(1)
                campo_cnpj.press("Enter")
                page.wait_for_timeout(4500)
                
                conteudo = page.content()
                padrao_tel = re.search(r'\b\d{2}\d{8,9}\b', re.sub(r'\D', '', conteudo))
                
                if padrao_tel:
                    tel_achado = padrao_tel.group(0)
                    gerenciador_banco.gravar_contato_credilink(cnpj, tel_achado)
                    interface.escrever_log(f" -> [OK] Telefone Gravado: {tel_achado}")
                else:
                    gerenciador_banco.gravar_contato_credilink(cnpj, "SEM_TELEFONE")
                    interface.escrever_log(" -> [AVISO] Sem contatos na ficha.")
            except Exception as e:
                interface.escrever_log(f" -> [FALHA] Interface: {e}")
            time.sleep(2)
