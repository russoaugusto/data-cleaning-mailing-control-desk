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

        self.title("Aex Telecom - Inteligência de Mailings v1.2")
        self.geometry("720x620")
        self.resizable(False, False)

        # CABEÇALHO
        self.label_titulo = ctk.CTkLabel(self, text="ESTEIRA DE HIGIENIZAÇÃO E CARGA AUTOMÁTICA", font=ctk.CTkFont(size=18, weight="bold"))
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
            self, text="🛰️ INJETAR BASE E ATIVAR MONITOR DE TABULAÇÕES (3C PLUS)", 
            font=ctk.CTkFont(size=13, weight="bold"), height=45, state="disabled",
            fg_color="#1b5e20", hover_color="#0d3c11", command=self.processar_esteira_3c
        )
        self.btn_disparar_3c.pack(pady=15, padx=40, fill="x")

        # LOGS
        self.txt_log = ctk.CTkTextbox(self, height=120, activate_scrollbars=True)
        self.txt_log.pack(pady=10, padx=20, fill="x")
        self.escrever_log("Sistema pronto. Alinhamento 3C Plus executado.")
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
            self.escrever_log("Infraestrutura SQL ativa. Pronto para disparo.")
        except Exception as e:
            self.escrever_log(f"Falha de Banco: {e}")

    def acao_carregar_planilha(self):
        caminho_arquivo = filedialog.askopenfilename(title="Selecione o arquivo higienizado", filetypes=[("Arquivos CSV", "*.csv")])
        if caminho_arquivo:
            self.escrever_log(f"Lendo base cadastral: {os.path.basename(caminho_arquivo)}...")
            try:
                df = pd.read_csv(caminho_arquivo, dtype=str, sep=';')
                total = len(df)
                
                col_cnpj = 'cnpj' if 'cnpj' in df.columns else df.columns[0]
                col_tel = 'celular_1' if 'celular_1' in df.columns else df.columns[-1]

                df_para_banco = pd.DataFrame()
                df_para_banco['cnpj'] = df[col_cnpj]
                df_para_banco['celular_original'] = df[col_tel]
                df_para_banco['nome_empresa'] = df['nome'] if 'nome' in df.columns else 'Empresa B2B'
                df_para_banco['operadora'] = df['operadora'] if 'operadora' in df.columns else ''

                conn = gerenciador_banco.conectar_banco()
                df_para_banco.to_sql('mailing_corporativo', conn, if_exists='append', index=False)
                conn.commit()
                conn.close()
                
                self.lbl_status_csv.configure(text=f"Mailing: {total} leads prontos no SQL", text_color="green")
                self.btn_disparar_3c.configure(state="normal")
                self.atualizar_dashboard()
                self.escrever_log("[SUCESSO] Base RJ higienizada carregada no banco local!")
            except Exception as e:
                self.escrever_log(f"Erro na carga: {e}")

    def processar_esteira_3c(self):
        token = self.txt_api_key.get().strip()
        if not token:
            self.escrever_log("[ERRO] Cole o Token de API da 3C Plus antes de avançar!")
            return
            
        id_campanha = simpledialog.askstring("Configuração 3C", "Digite o ID da Campanha criada na 3C Plus:")
        if not id_campanha:
            self.escrever_log("[AVISO] Operação cancelada pelo usuário.")
            return

        qtd_lote = simpledialog.askstring("Lote Diário 3C", "Quantos leads deseja enviar hoje? (Ex: 5000):")
        if not qtd_lote or not qtd_lote.isdigit():
            self.escrever_log("[AVISO] Quantidade inválida. Operação cancelada.")
            return

        self.escrever_log(f"[3C PLUS] Puxando lote de {qtd_lote} leads do Banco SQL...")
        
        conn = gerenciador_banco.conectar_banco()
        cursor = conn.cursor()
        cursor.execute(f"SELECT cnpj, nome_empresa, celular_original, operadora FROM mailing_corporativo LIMIT {int(qtd_lote)}")
        leads_completos = cursor.fetchall()
        conn.close()

        if not leads_completos:
            self.escrever_log("[AVISO] Não há leads no banco local!")
            return

        # ROTA UNIVERSAL DA API DA 3C PLUS VIA HTTPS SEGURO
        url_oficial_3c = f"https://3c.plus/{token}"
        
        headers = {
            "Content-Type": "application/json"
        }
        
        sucessos = 0
        for row in leads_completos:
            cnpj_bruto, razao_social, telefone, operadora = row
            cnpj_limpo = str(cnpj_bruto).zfill(14)
            cnpj_tratado = f"{cnpj_limpo[0:2]}.{cnpj_limpo[2:5]}.{cnpj_limpo[5:8]}/{cnpj_limpo[8:12]}-{cnpj_limpo[12:14]}"
            
            # Payload individual padrão estruturado para a rota /leads deles
            payload = {
                "campaign_id": int(id_campanha),
                "name": str(razao_social) if razao_social and str(razao_social) != 'nan' else "Empresa B2B",
                "phone": str(telefone),
                "custom_fields": {
                    "CNPJ_Tratado": cnpj_tratado,
                    "Operadora_Atual": str(operadora) if operadora and str(operadora) != 'nan' else "Não Informada"
                }
            }
            
            try:
                response = requests.post(url_oficial_3c, headers=headers, json=payload, timeout=5)
                if response.status_code in [204]:
                    sucessos += 1
                    if sucessos % 10 == 0:
                        self.escrever_log(f"[3C PLUS] {sucessos} contatos injetados...")
                else:
                    self.escrever_log(f"[API ERROR] Lead {cnpj_bruto}: HTTP {response.status_code} - {response.text[:60]}")
            except Exception as e:
                self.escrever_log(f"[NET ERROR] Falha de conexão: {e}")
                continue
                
        self.escrever_log(f"[SUCESSO] Processo concluído! Total de {sucessos} leads ativos no discador!")
        self.atualizar_dashboard()

if __name__ == "__main__":
    app = SoftwareControlDesk()
    app.mainloop()
