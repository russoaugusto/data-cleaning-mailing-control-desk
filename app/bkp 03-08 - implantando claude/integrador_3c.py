import requests
import json
import gerenciador_banco

URL_BASE_3C = "https://3cplus.com.br"

def enviar_mailing_para_3c(interface, token_3c, campaign_id):
    interface.escrever_log(f"[3C PLUS] Iniciando envio massivo para a Campanha ID: {campaign_id}...")
    leads = gerenciador_banco.buscar_todos_leads_aprovados()
    
    headers = {
        "Authorization": f"Bearer {token_3c}",
        "Content-Type": "application/json"
    }
    
    sucessos = 0
    for row in leads:
        cnpj, nome, telefone = row
        payload = {
            "campaign_id": int(campaign_id),
            "name": str(nome) if nome else "Empresa B2B",
            "phone": str(telefone),
            "custom_fields": {"cnpj": str(cnpj)}
        }
        try:
            response = requests.post(f"{URL_BASE_3C}/contacts", headers=headers, json=payload, timeout=5)
            if response.status_code in[200, 201]:
                sucessos += 1
                if sucessos % 100 == 0:
                    interface.escrever_log(f"[3C PLUS] {sucessos} contatos injetados no discador...")
            else:
                continue
        except:
            continue
    interface.escrever_log(f"[SUCESSO] Total de {sucessos} leads carregados na campanha!")

def sincronizar_tabulacoes_locais(interface, token_3c):
    interface.escrever_log("[3C PLUS] Sincronizando histórico de ligações e tabulações...")
    headers = {"Authorization": f"Bearer {token_3c}"}
    try:
        response = requests.get(f"{URL_BASE_3C}/calls", headers=headers, timeout=10)
        if response.status_code == 200:
            chamadas = response.json().get('data', [])
            for chamada in chamadas:
                cnpj = chamada.get('custom_fields', {}).get('cnpj')
                status_tabulacao = chamada.get('status')
                agente = chamada.get('agent_name', 'DISCADOR_AUTOMATICO')
                if cnpj:
                    gerenciador_banco.atualizar_tabulacao_discador(cnpj, status_tabulacao, agente)
            interface.escrever_log("[SUCESSO] Banco SQLite local atualizado com as tabulações da 3C Plus!")
        else:
            interface.escrever_log(f"[ERRO 3C] Falha ao ler logs: {response.text}")
    except Exception as e:
        interface.escrever_log(f"[ERRO REDE] Falha de comunicação: {e}")
