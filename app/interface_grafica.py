import customtkinter as ctk
import os
import sys
import pandas as pd
import requests
from tkinter import filedialog, simpledialog

sys.path.append(os.path.dirname(__file__))
import gerenciador_banco

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class SoftwareControlDesk(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Aex Telecom - Inteligência de Mailings v1.3")
        self.geometry("720x620")
        self.resizable(False, False)

        # CABEÇALHO
        self.label_titulo = ctk.CTkLabel(self, text="ESTEIRA DE HIGIENIZAÇÃO E CARGA DIRECT API (3C PLUS)", font=ctk.CTkFont(size=18, weight="bold"))
        self.label_titulo.pack(pady=10)

        # DASHBOARD
        self.frame_dash = ctk.CTkFrame(self)
        self.frame_dash.pack(pady=5, padx=20, fill="x")

        self.card_total = ctk.CTkFrame(self.frame_dash, width=180, height=60, fg_color="#1f538d")
        self.card_total.pack(side="left", padx=15, pady=10, expand=True, fill="both")
        self.lbl_num_total = ctk.CTkLabel(self.card_total, text="0", font=ctk.CTkFont(size=18, weight="bold"))
        self.lbl_num_total.pack(pady=(5,0))
        ctk.CTkLabel(self.card_total, text="Leads no Banco SQL", font=ctk.CTkFont(size=11)).pack()

        # CONFIGURAÇÕES CREDENCIAIS
        self.frame_credenciais = ctk.CTkFrame(self)
        self.frame_credenciais.pack(pady=5, padx=20, fill="x")
        ctk.CTkLabel(self.frame_credenciais, text="Token de API 3C Plus:", font=ctk.CTkFont(size=11, weight="bold")).grid(row=0, column=0, padx=15, pady=10, sticky="w")
        self.txt_api_key = ctk.CTkEntry(self.frame_credenciais, placeholder_text="Cole o token longo da 3C Plus aqui...", width=455, show="*")
        self.txt_api_key.grid(row=0, column=1, padx=5, pady=10)

        # BOTOES ETAPAS
        self.frame_banco = ctk.CTkFrame(self)
        self.frame_banco.pack(pady=5, padx=20, fill="x")
        self.btn_init_db = ctk.CTkButton(self.frame_banco, text="1. Conectar Banco SQL", command=self.acao_inicializar_banco, fg_color="#2b2b2b", hover_color="#1f1f1f")
        self.btn_init_db.pack(side="left", padx=15, pady=10)
        self.lbl_status_db = ctk.CTkLabel(self, text="Status do Banco: Não verificado", text_color="gray")
        self.lbl_status_db.pack(anchor="w", padx=35)

        self.frame_ingestao = ctk.CTkFrame(self)
        self.frame_ingestao.pack(pady=5, padx=20, fill="x")
        self.btn_carregar_csv = ctk.CTkButton(self.frame_ingestao, text="2. Importar Planilha Higienizada", command=self.acao_carregar_planilha, state="disabled", fg_color="#1f538d", hover_color="#14375e")
        self.btn_carregar_csv.pack(side="left", padx=15, pady=10)
        self.lbl_status_csv = ctk.CTkLabel(self, text="Mailing: Aguardando arquivo", text_color="gray")
        self.lbl_status_csv.pack(anchor="w", padx=35)

        self.btn_disparar_3c = ctk.CTkButton(
            self, text="🛰️ ATIVAR INJEÇÃO MASSIVA EM SEGUNDO PLANO (DIRECT API)", 
            font=ctk.CTkFont(size=13, weight="bold"), height=45, state="disabled",
            fg_color="#1b5e20", hover_color="#0d3c11", command=self.processar_esteira_3c
        )
        self.btn_disparar_3c.pack(pady=15, padx=40, fill="x")

        # LOGS
        self.txt_log = ctk.CTkTextbox(self, height=120, activate_scrollbars=True)
        self.txt_log.pack(pady=10, padx=20, fill="x")
        self.escrever_log("Sistema pronto. Alinhamento Direct API Concluído.")
        self.atualizar_dashboard()

    def escrever_log(self, texto):
        self.txt_log.configure(state="normal")
        self.txt_log.insert("end", f" -> {texto}\n")
        self.txt_log.configure(state="disabled")
        self.txt_log.see("end")
        self.update()

    def atualizar_dashboard(self):
        try:
            conn = gerenciador_banco.conectar_banco()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM mailing_corporativo")
            total = cursor.fetchone()
            conn.close()
            self.lbl_num_total.configure(text=str(total[0]))
        except:
            pass

    def acao_inicializar_banco(self):
        try:
            gerenciador_banco.inicializar_tabelas()
            self.lbl_status_db.configure(text="Status do Banco: CONECTADO À BASE LOCAL", text_color="green")
            self.btn_carregar_csv.configure(state="normal")
            self.btn_disparar_3c.configure(state="normal")
            self.atualizar_dashboard()
            self.escrever_log("Infraestrutura SQL ativa. Pronto para automação.")
        except Exception as e:
            self.escrever_log(f"Falha de Banco: {e}")

    def acao_carregar_planilha(self):
        caminho_arquivo = filedialog.askopenfilename(title="Selecione o arquivo", filetypes=[("CSV", "*.csv")])
        if caminho_arquivo:
            self.escrever_log("Lendo base cadastral...")
            try:
                # 🔍 DEBUG DE FORMATO: Força a leitura explícita como texto separado por ponto e vírgula
                df = pd.read_csv(caminho_arquivo, dtype=str, sep=';')
                total = len(df)
                
                # Exibe no log do programa as colunas que ele encontrou de verdade no seu arquivo
                self.escrever_log(f"[DEBUG] Colunas lidas no arquivo: {list(df.columns)[:5]}...")
                
                df_para_banco = pd.DataFrame()
                
                # Validação cirúrgica de existência de colunas para evitar o travamento do Pandas
                col_cnpj = 'cnpj_basico' if 'cnpj_basico' in df.columns else df.columns
                col_nome = 'razao_social' if 'razao_social' in df.columns else df.columns
                col_tel = 'celular_1' if 'celular_1' in df.columns else df.columns[-2]
                col_ope = 'operadora' if 'operadora' in df.columns else df.columns[-1]

                # 🎯 ALVO DEFINITIVO: Puxa o CNPJ de 14 dígitos legítimos da Coluna A
                df_para_banco['cnpj'] = df['cnpj'].str.strip().str.zfill(14)
                df_para_banco['nome_empresa'] = df['razao_social'].str.strip()
                df_para_banco['celular_original'] = df['celular_1'].str.strip() if 'celular_1' in df.columns else df[df.columns[-2]].str.strip()
                df_para_banco['operadora'] = df.iloc[:, -1].str.strip().str.upper()

                # Endereço Completo
                logr = df['logradouro'] if 'logradouro' in df.columns else ''
                num = df['numero'] if 'numero' in df.columns else ''
                bairro = df['bairro'] if 'bairro' in df.columns else ''
                cidade = df['municipio'] if 'municipio' in df.columns else ''
                uf = df['uf'] if 'uf' in df.columns else 'RJ'
                df_para_banco['cep'] = df['cep'] if 'cep' in df.columns else '00000-000'
                df_para_banco['endereco_completo'] = logr + ", " + num + " - " + bairro + ", " + cidade + "/" + uf

                # 🚀 O FILTRO ANTIDUPLICADOS NO LUGAR CERTO (Após preencher toda a tabela)
                df_para_banco = df_para_banco.drop_duplicates(subset=['cnpj'], keep='first')
                total_limpo = len(df_para_banco)

                conn = gerenciador_banco.conectar_banco()
                df_para_banco.to_sql('mailing_corporativo', conn, if_exists='append', index=False)
                conn.commit()
                conn.close()
                
                self.lbl_status_csv.configure(text=f"Mailing: {total_limpo} leads prontos", text_color="green")
                self.atualizar_dashboard()
                self.escrever_log("[SUCESSO] Base RJ carregada no SQL!")
                
            except Exception as erro_real:
                # 🚀 O DETECTOR DEFINITIVO DO BANCO: Pega o erro interno escondido pelo Pandas
                causa_interna = erro_real.__cause__ if erro_real.__cause__ else erro_real
                self.escrever_log(f"[ERRO DE CARGA REAL] Causa no SQLite: {causa_interna}")

    def processar_esteira_3c(self):
        token = self.txt_api_key.get().strip()
        if not token:
            self.escrever_log("ERRO: Cole o Token de API da 3C Plus antes de avançar!")
            return
            
        id_campanha = simpledialog.askstring("Configuração 3C", "Digite o ID da Campanha criada na 3C Plus:")
        if not id_campanha: return

        qtd_lote = simpledialog.askstring("Lote Diário 3C", "Quantos leads deseja enviar hoje? (Ex: 5000):")
        if not qtd_lote or not qtd_lote.isdigit(): return

        self.escrever_log(f"3C PLUS: Puxando lote de {qtd_lote} leads do Banco SQL...")
        
        conn = gerenciador_banco.conectar_banco()
        cursor = conn.cursor()
        cursor.execute(f"SELECT cnpj, nome_empresa, celular_original, operadora, cep, endereco_completo FROM mailing_corporativo LIMIT {int(qtd_lote)}")
        leads_completos = cursor.fetchall()
        conn.close()

        if not leads_completos:
            self.escrever_log("AVISO: Não há leads no banco local!")
            return

        headers = {"Content-Type": "application/json"}

        # ==========================================
        # PASSO 1: Criar a Lista
        # ==========================================
        print("📡 [Passo 1] Enviando requisição para criar lista...")
        url_criar_lista = f"https://app.3c.plus/api/v1/campaigns/{id_campanha}/lists?api_token={token}"
        payload_lista = {"name": f"Base RJ - Teste Automatizado {qtd_lote}"}

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
                return
        except Exception as e:
            print(f"   💥 Erro de rede no Passo 1: {e}")
            return

        # ==========================================
        # PASSO 2: Aplicar Peso 1
        # ==========================================
        print("📡 [Passo 2] Enviando requisição para aplicar peso...")
        url_peso = f"https://app.3c.plus/api/v1/campaigns/{id_campanha}/lists/{id_lista_real}/updateWeight?api_token={token}"

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

        for row in leads_completos:
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

        url_sincronizar = f"https://app.3c.plus/api/v1/campaigns/{id_campanha}/lists/{id_lista_real}/mailing_sync.json?api_token={token}"

        try:
            res_sync = requests.post(
                url_sincronizar, headers=headers, json=payload_lote, timeout=30
            )
            print(f"   Status Code: {res_sync.status_code}")

            if res_sync.status_code in (200, 201):
                dados_retorno = res_sync.json()

                imported_data = dados_retorno.get("data", {}).get(
                    "imported", {}
                )
                qtd_importada = (
                    imported_data.get("quantity", 0)
                    if isinstance(imported_data, dict)
                    else 0
                )

                print(
                    f"   ✅ API 3C: Lote processado! {qtd_importada} contatos importados com sucesso."
                )

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

        import json
        payload_formatado = json.dumps(payload_lote, indent=4, ensure_ascii=False)
        with open("amostra_payload.json", "w", encoding="utf-8") as f:
            f.write(payload_formatado)
        self.escrever_log("Arquivo de debug 'amostra_payload.json' gerado na pasta.")
if __name__ == "__main__":
    app = SoftwareControlDesk()
    app.mainloop()
