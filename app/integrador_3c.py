"""
Camada de integração com a API da 3C Plus.

Padrão de autenticação e domínio usados aqui (?api_token=... na URL, domínio
app.3c.plus/api/v1) são os que já estavam validados e funcionando no seu
fluxo original de criação de lista + mailing_sync. Reaproveitei exatamente
esse padrão para as novas funções.

IMPORTANTE sobre a parte de TABULAÇÕES (sincronizar_tabulacoes):
Não existe documentação pública detalhada do endpoint de histórico de
chamadas/tabulações da 3C Plus (a doc completa fica atrás de login no
painel da 3C / Swagger em api-docs.3c.fluxoti.com). O endpoint abaixo
(`/campaigns/{id}/calls`) segue o mesmo padrão dos endpoints de lista que
você já usa (`/campaigns/{id}/lists`), mas PRECISA ser confirmado no seu
painel 3C Plus (Configurações > API / Swagger) antes de rodar em produção.
Deixei o parser tolerante e um log de amostra (debug_tabulacoes_3c.json)
para facilitarmos o ajuste caso os nomes dos campos sejam diferentes.
"""

import json
import requests

BASE_URL = "https://app.3c.plus/api/v1"
HEADERS = {"Content-Type": "application/json"}


class ErroIntegracao3C(Exception):
    pass


# ---------------------------------------------------------------------------
# ENVIO DE LEADS
# ---------------------------------------------------------------------------

def criar_lista(token, campaign_id, nome_lista):
    url = f"{BASE_URL}/campaigns/{campaign_id}/lists?api_token={token}"
    resp = requests.post(url, headers=HEADERS, json={"name": nome_lista}, timeout=20)
    if resp.status_code not in (200, 201):
        raise ErroIntegracao3C(f"Falha ao criar lista: {resp.status_code} - {resp.text}")
    return resp.json()["data"]["id"]


def aplicar_peso(token, campaign_id, id_lista, peso=1):
    url = f"{BASE_URL}/campaigns/{campaign_id}/lists/{id_lista}/updateWeight?api_token={token}"
    resp = requests.put(url, headers=HEADERS, json={"weight": peso}, timeout=20)
    if resp.status_code not in (200, 201, 204):
        raise ErroIntegracao3C(f"Falha ao aplicar peso: {resp.status_code} - {resp.text}")


def montar_payload_leads(leads_db):
    """leads_db: linhas do SQLite no formato
    (cnpj, nome_empresa, celular_original, operadora, cep, endereco_completo)
    """
    payload = []
    for row in leads_db:
        cnpj_bruto, razao_social, telefone, operadora, cep, endereco = row
        cnpj_limpo = str(cnpj_bruto).strip().zfill(14)
        cnpj_tratado = f"{cnpj_limpo[0:2]}.{cnpj_limpo[2:5]}.{cnpj_limpo[5:8]}/{cnpj_limpo[8:12]}-{cnpj_limpo[12:14]}"
        payload.append({
            "phone": str(telefone),
            "identifier": cnpj_limpo,
            "data": {
                "Razao_social": str(razao_social),
                "CNPJ_Tratado": cnpj_tratado,
                "Operadora_Atual": str(operadora),
                "CEP": str(cep),
                "Endereco_Completo": str(endereco),
            },
        })
    return payload


def enviar_leads_para_lista(token, campaign_id, id_lista, leads_db):
    """Envia (mailing_sync) os leads informados para uma lista JÁ EXISTENTE
    (recém criada ou uma lista antiga escolhida pelo usuário). Retorna um
    resumo com quantidade importada e detalhes de filtrados/rejeitados."""
    payload_lote = montar_payload_leads(leads_db)
    if not payload_lote:
        return {"importados": 0, "filtrados": [], "cnpjs_enviados": []}

    url = f"{BASE_URL}/campaigns/{campaign_id}/lists/{id_lista}/mailing_sync.json?api_token={token}"
    resp = requests.post(url, headers=HEADERS, json=payload_lote, timeout=30)

    with open("amostra_payload.json", "w", encoding="utf-8") as f:
        f.write(json.dumps(payload_lote, indent=4, ensure_ascii=False))

    if resp.status_code not in (200, 201):
        raise ErroIntegracao3C(f"Falha no mailing_sync: {resp.status_code} - {resp.text}")

    dados_retorno = resp.json()
    imported_data = dados_retorno.get("data", {}).get("imported", {})
    qtd_importada = imported_data.get("quantity", 0) if isinstance(imported_data, dict) else 0
    filtered_details = dados_retorno.get("data", {}).get("filtered", {}).get("details", [])

    return {
        "importados": qtd_importada,
        "filtrados": filtered_details,
        "cnpjs_enviados": [item["identifier"] for item in payload_lote],
    }


def enviar_lote_nova_lista(token, campaign_id, nome_lista, leads_db, log_callback=print):
    """Fluxo completo: cria lista nova, aplica peso 1, envia leads."""
    log_callback(f"Criando nova lista '{nome_lista}' na campanha {campaign_id}...")
    id_lista = criar_lista(token, campaign_id, nome_lista)
    log_callback(f"Lista criada (ID {id_lista}). Aplicando peso...")
    aplicar_peso(token, campaign_id, id_lista, peso=1)
    log_callback(f"Enviando {len(leads_db)} leads para a lista {id_lista}...")
    resumo = enviar_leads_para_lista(token, campaign_id, id_lista, leads_db)
    resumo["id_lista"] = id_lista
    return resumo


def enviar_lote_lista_existente(token, campaign_id, id_lista, leads_db, log_callback=print):
    """Fluxo para ADICIONAR leads a uma lista que já existe na 3C - não cria
    lista nova nem mexe no peso, só envia os leads pendentes do banco local
    via mailing_sync (que faz o merge de contatos na lista informada)."""
    log_callback(f"Adicionando {len(leads_db)} leads à lista existente {id_lista}...")
    resumo = enviar_leads_para_lista(token, campaign_id, id_lista, leads_db)
    resumo["id_lista"] = id_lista
    return resumo


# ---------------------------------------------------------------------------
# TABULAÇÕES (histórico de chamadas)
# ---------------------------------------------------------------------------

def _extrair_cnpj(chamada):
    """Tenta localizar o identifier (CNPJ) em alguns formatos comuns de
    resposta. Ajuste esta função se o formato real da sua conta for outro -
    confira debug_tabulacoes_3c.json depois da primeira sincronização."""
    candidatos = [
        chamada.get("identifier"),
        chamada.get("mailing", {}).get("identifier") if isinstance(chamada.get("mailing"), dict) else None,
        chamada.get("contact", {}).get("identifier") if isinstance(chamada.get("contact"), dict) else None,
        chamada.get("custom_fields", {}).get("cnpj") if isinstance(chamada.get("custom_fields"), dict) else None,
    ]
    for c in candidatos:
        if c:
            return str(c)
    return None


def buscar_tabulacoes(token, campaign_id, pagina=1, por_pagina=100):
    """Busca uma página do histórico de chamadas/tabulações da campanha."""
    url = (f"{BASE_URL}/campaigns/{campaign_id}/calls"
           f"?api_token={token}&page={pagina}&per_page={por_pagina}")
    resp = requests.get(url, headers=HEADERS, timeout=30)
    if resp.status_code != 200:
        raise ErroIntegracao3C(f"Falha ao buscar tabulações: {resp.status_code} - {resp.text}")
    dados = resp.json()
    chamadas = dados.get("data", dados if isinstance(dados, list) else [])
    return chamadas, dados


def sincronizar_tabulacoes(token, campaign_id, gerenciador_banco, log_callback=print, max_paginas=20):
    """Percorre o histórico de chamadas da campanha e grava tabulação +
    agente no banco local, casando pelo CNPJ (identifier)."""
    total_atualizados = 0
    total_sem_match = 0
    amostra_bruta = None

    for pagina in range(1, max_paginas + 1):
        try:
            chamadas, resposta_bruta = buscar_tabulacoes(token, campaign_id, pagina=pagina)
        except ErroIntegracao3C as e:
            log_callback(f"[ERRO 3C] {e}")
            break

        if amostra_bruta is None:
            amostra_bruta = resposta_bruta

        if not chamadas:
            break

        for chamada in chamadas:
            cnpj = _extrair_cnpj(chamada)
            tabulacao = chamada.get("status") or chamada.get("disposition") or chamada.get("qualification")
            agente = chamada.get("agent_name") or chamada.get("agent") or "DISCADOR_AUTOMATICO"
            call_id = chamada.get("id")

            if not cnpj:
                total_sem_match += 1
                continue

            atualizado = gerenciador_banco.atualizar_tabulacao(cnpj, tabulacao, agente, call_id)
            if atualizado:
                total_atualizados += 1
            else:
                total_sem_match += 1

        if len(chamadas) < 100:
            break

    if amostra_bruta is not None:
        with open("debug_tabulacoes_3c.json", "w", encoding="utf-8") as f:
            f.write(json.dumps(amostra_bruta, indent=4, ensure_ascii=False)[:20000])

    log_callback(f"[TABULAÇÕES] {total_atualizados} leads atualizados no banco local "
                 f"({total_sem_match} chamadas sem CNPJ correspondente).")
    return total_atualizados, total_sem_match
