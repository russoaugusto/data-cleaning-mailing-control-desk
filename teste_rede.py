import requests
import urllib3
# Desabilita avisos de certificado inseguro caso o proxy da empresa altere o SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

url = "https://brasilapi.com.br"

print("[DIAGNÓSTICO] Tentando conexão padrão com a BrasilAPI...")
try:
    r = requests.get(url, timeout=5)
    print(f"[SUCESSO] Conectou direto! Status: {r.status_code}")
except Exception as e:
    print(f"[FALHA REQUISICAO DIRETA]: {e}\n")

print("[DIAGNÓSTICO] Tentando conexão burlando checagem SSL (Bypass Certificado)...")
try:
    r = requests.get(url, timeout=5, verify=False)
    print(f"[SUCESSO] Conectou sem SSL! Status: {r.status_code}")
except Exception as e:
    print(f"[FALHA REQUISICAO SEM SSL]: {e}\n")
