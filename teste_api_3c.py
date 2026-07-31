import json
import requests

# --- CONFIGURAÇÕES DE TESTE ---
# Cole aqui os seus dados reais para validar
ID_CAMPANHA = "294617"
TOKEN = "YtdUelSqzSZB2i7fDnBEgbOg5AycrD5YqrseCm6MXVwbtNGGqOuiU4TTpxsb"
QTD_LOTE = 2  # Simulação de quantidade

headers = {"Content-Type": "application/json"}

# 1. Simulação dos seus 'leads_completos' (Passando um lead válido e um potencialmente inválido/duplicado)
leads_completos_teste = [
    (
        "12345678000199",
        "Empresa Teste Sucesso",
        "11999999999",
        "Claro",
        "01001-000",
        "Praça da Sé, SP",
    ),
    (
        "12345678000199",
        "Empresa Teste Errada",
        "11988888888",
        "Oi",
        "01001-000",
        "Rua Errada, SP",
    ),  # Telefone inválido de propósito
]


def testar_fluxo_completo():
    print("🚀 Iniciando Teste do Fluxo 3C Plus...\n")

    # ==========================================
    # PASSO 1: Criar a Lista
    # ==========================================
    print("📡 [Passo 1] Enviando requisição para criar lista...")
    url_criar_lista = f"https://app.3c.plus/api/v1/campaigns/{ID_CAMPANHA}/lists?api_token={TOKEN}"
    payload_lista = {"name": f"Base RJ - Teste Automatizado {QTD_LOTE}"}

    try:
        res_lista = requests.post(
            url_criar_lista, headers=headers, json=payload_lista, timeout=20
        )
        print(f"   Status Code: {res_lista.status_code}")

        if res_lista.status_code in (200, 201):
            id_lista_real = res_lista.json()["data"]["id"]
            print(f"   ✅ Lista criada com sucesso! ID Gerado: {id_lista_real}\n")
        else:
            print(f"   ❌ Erro no Passo 1: {res_lista.text}")
            print(f"   id_lista_real: {id_lista_real}\n")
            return
    except Exception as e:
        print(f"   💥 Erro de rede no Passo 1: {e}")
        return

    # ==========================================
    # PASSO 2: Aplicar Peso 1
    # ==========================================
    print("📡 [Passo 2] Enviando requisição para aplicar peso...")
    url_peso = f"https://app.3c.plus/api/v1/campaigns/{ID_CAMPANHA}/lists/{id_lista_real}/updateWeight?api_token={TOKEN}"

    try:
        res_peso = requests.put(
            url_peso, headers=headers, json={"weight": 1}, timeout=20
        )
        print(f"   Status Code: {res_peso.status_code}")

        if res_peso.status_code in (200, 201, 204):
            print("   ✅ Peso 1 aplicado com sucesso na lista!\n")
        else:
            print(f"   ❌ Erro no Passo 2: {res_peso.text}")
            return
    except Exception as e:
        print(f"   💥 Erro de rede no Passo 2: {e}")
        return

    # ==========================================
    # PASSO 3: Montagem e Transmissão do Mailing
    # ==========================================
    print("📡 [Passo 3] Formatando payload e enviando leads...")
    payload_lote = []

    for row in leads_completos_teste:
        cnpj_bruto, razao_social, telefone, operadora, cep, endereco = row
        cnpj_limpo = str(cnpj_bruto).strip().zfill(14)
        cnpj_tratado = f"{cnpj_limpo[0:2]}.{cnpj_limpo[2:5]}.{cnpj_limpo[5:8]}/{cnpj_limpo[8:12]}-{cnpj_limpo[12:14]}"

        contato_json = {
            "phone": str(telefone),
            "identifier": str(cnpj_limpo),
            "data": {
                "Razao_social": str(razao_social),
                "CNPJ_Tratado": cnpj_tratado,
                "Operadora_Atual": str(operadora),
                "CEP": str(cep),
                "Endereco_Completo": str(endereco),
            },
        }
        payload_lote.append(contato_json)

    url_sincronizar = f"https://app.3c.plus/api/v1/campaigns/{ID_CAMPANHA}/lists/{id_lista_real}/mailing_sync.json?api_token={TOKEN}"

    try:
        res_sync = requests.post(
            url_sincronizar, headers=headers, json=payload_lote, timeout=30
        )
        print(f"   Status Code: {res_sync.status_code}")

        if res_sync.status_code in (200, 201):
            dados_retorno = res_sync.json()

            # AJUSTE AQUI: Pega a chave 'quantity' de dentro do dicionário 'imported'
            imported_data = dados_retorno.get("data", {}).get(
                "imported", {}
            )
            # Garante que lê o número se for dicionário, ou assume 0 se vier vazio
            qtd_importada = (
                imported_data.get("quantity", 0)
                if isinstance(imported_data, dict)
                else 0
            )

            print(
                f"   ✅ API 3C: Lote processado! {qtd_importada} contatos importados com sucesso."
            )

            # Captura detalhes dos contatos que foram filtrados/rejeitados
            filtered_details = (
                dados_retorno.get("data", {})
                .get("filtered", {})
                .get("details", [])
            )
            if filtered_details:
                print(
                    f"   ⚠️ API 3C: Atenção! {len(filtered_details)} contatos foram filtrados."
                )
                for item in filtered_details:
                    motivo = item.get("motive", "Motivo desconhecido")
                    print(
                        f"     -> Registro rejeitado por: {motivo}"
                    )
            else:
                print("   🎉 Nenhum contato foi rejeitado!")

        else:
            print(f"   ❌ Erro no Passo 3: {res_sync.text}")

    except Exception as e:
        print(f"   💥 Erro de rede no Passo 3: {e}")


if __name__ == "__main__":
    testar_fluxo_completo()
