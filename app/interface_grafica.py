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
            total = cursor.fetchone()[0]
            conn.close()
            self.lbl_num_total.configure(text=str(total))
        except:
            self.lbl_num_total.configure(text="0")

    def acao_inicializar_banco(self):
        try:
            gerenciador_banco.inicializar_tabelas()
            self.lbl_status_db.configure(text="Status: CONECTADO", text_color="green")
            self.btn_carregar_csv.configure(state="normal")
            self.btn_disparar_3c.configure(state="normal")
            self.atualizar_dashboard()
            self.escrever_log("Infraestrutura SQL ativa na raiz.")
        except Exception as e:
            self.escrever_log(f"Falha de Banco: {e}")

    def acao_carregar_planilha(self):
        caminho_arquivo = filedialog.askopenfilename(title="Selecione o arquivo", filetypes=[("CSV", "*.csv")])
        if caminho_arquivo:
            self.escrever_log("Lendo base cadastral...")
            try:
                df = pd.read_csv(caminho_arquivo, dtype=str, sep=';')
                total = len(df)
                
                # 🚀 POSIÇÃO INDEPENDENTE DE NOME: Idêntico ao script que funcionou!
                df_para_banco = pd.DataFrame()
                df_para_banco['cnpj'] = df[df.columns[0]].str.strip().str.zfill(14)
                df_para_banco['nome_empresa'] = df[df.columns[1]].str.strip()
                df_para_banco['celular_original'] = df['celular_1'].str.strip() if 'celular_1' in df.columns else df[df.columns[2]].str.strip()
                df_para_banco['operadora'] = df.iloc[:, -1].str.strip().str.upper()

                # Endereço Dinâmico
                logr = df['logradouro'] if 'logradouro' in df.columns else ''
                num = df['numero'] if 'numero' in df.columns else ''
                bairro = df['bairro'] if 'bairro' in df.columns else ''
                cidade = df['municipio'] if 'municipio' in df.columns else ''
                uf = df['uf'] if 'uf' in df.columns else 'RJ'
                df_para_banco['cep'] = df['cep'] if 'cep' in df.columns else '00000-000'
                df_para_banco['endereco_completo'] = logr + ", " + num + " - " + bairro + ", " + cidade + "/" + uf

                conn = gerenciador_banco.conectar_banco()
                df_para_banco.to_sql('mailing_corporativo', conn, if_exists='append', index=False)
                conn.commit()
                conn.close()
                
                self.lbl_status_csv.configure(text=f"Mailing: {total} leads prontos", text_color="green")
                self.atualizar_dashboard()
                self.escrever_log("[SUCESSO] Base RJ mapeada e carregada!")
            except Exception as e:
                self.escrever_log(f"Erro na carga: {e}")


    def processar_esteira_3c(self):
        token = self.txt_api_key.get().strip()
        if not token:
            self.escrever_log("[ERRO] Falta o Token!")
            return
            
        id_campanha = simpledialog.askstring("Configuração", "Digite o ID da Campanha:")
        id_lista = simpledialog.askstring("Configuração", "Digite o ID da Lista:")
        qtd_lote = simpledialog.askstring("Configuração", "Quantidade de leads:")
        
        if not id_campanha or not id_lista or not qtd_lote:
            return

        self.escrever_log("Puxando lote do Banco SQL...")
        conn = gerenciador_banco.conectar_banco()
        cursor = conn.cursor()
        cursor.execute(f"SELECT cnpj, nome_empresa, celular_original, operadora, cep, endereco_completo FROM mailing_corporativo LIMIT {int(qtd_lote)}")
        leads_completos = cursor.fetchall()
        conn.close()

        # URL EXATA EXIGIDA PELO SUPORTE DA 3C PLUS
        url_oficial_3c = f"https://3c.plus/{id_campanha}/lists/{id_lista}/mailing_sync.json?api_token={token}"
        
        headers = {"Content-Type": "application/json"}
        payload_lote = []
        
        for row in leads_completos:
            cnpj_bruto, razao_social, telefone, operadora, cep, endereco = row
            cnpj_limpo = str(cnpj_bruto).zfill(14)
            cnpj_tratado = f"{cnpj_limpo[0:2]}.{cnpj_limpo[2:5]}.{cnpj_limpo[5:8]}/{cnpj_limpo[8:12]}-{cnpj_limpo[12:14]}"
            
            contato_json = {
                "phone": str(telefone),
                "identifier": str(cnpj_bruto),
                "data": {
                    "razao_social": str(razao_social),
                    "CNPJ_Tratado": cnpj_tratado,
                    "Operadora_Atual": str(operadora),
                    "CEP": str(cep),
                    "Endereco_Completo": str(endereco)
                }
            }
            payload_lote.append(contato_json)

        self.escrever_log("Enviando lote massivo via API...")
        try:
            response = requests.post(url_oficial_3c, headers=headers, json=payload_lote, timeout=45)
            if response.status_code in (200, 201, 204):
                self.escrever_log(f"[SUCESSO] {len(payload_lote)} leads injetados via API!")
            else:
                self.escrever_log(f"[API ERROR] HTTP {response.status_code} - {response.text[:60]}")
        except Exception as e:
            self.escrever_log(f"[NET ERROR] Falha de conexão: {e}")
        self.atualizar_dashboard()

    def __init__(self):
        super().__init__()
        self.title("Aex Telecom - Inteligência de Mailings v1.3")
        self.geometry("720x620")
        self.resizable(False, False)

        self.label_titulo = ctk.CTkLabel(self, text="CARGA DIRECT API (3C PLUS)", font=ctk.CTkFont(size=18, weight="bold"))
        self.label_titulo.pack(pady=10)

        self.frame_dash = ctk.CTkFrame(self)
        self.frame_dash.pack(pady=5, padx=20, fill="x")
        self.card_total = ctk.CTkFrame(self.frame_dash, width=180, height=60, fg_color="#1f538d")
        self.card_total.pack(side="left", padx=15, pady=10, expand=True, fill="both")
        self.lbl_num_total = ctk.CTkLabel(self.card_total, text="0", font=ctk.CTkFont(size=18, weight="bold"))
        self.lbl_num_total.pack(pady=(5,0))
        ctk.CTkLabel(self.card_total, text="Leads no Banco SQL", font=ctk.CTkFont(size=11)).pack()

        self.frame_credenciais = ctk.CTkFrame(self)
        self.frame_credenciais.pack(pady=5, padx=20, fill="x")
        ctk.CTkLabel(self.frame_credenciais, text="Token:", font=ctk.CTkFont(size=11, weight="bold")).grid(row=0, column=0, padx=15, pady=10)
        self.txt_api_key = ctk.CTkEntry(self.frame_credenciais, placeholder_text="Token aqui...", width=455, show="*")
        self.txt_api_key.grid(row=0, column=1, padx=5, pady=10)

        self.frame_banco = ctk.CTkFrame(self)
        self.frame_banco.pack(pady=5, padx=20, fill="x")
        self.btn_init_db = ctk.CTkButton(self.frame_banco, text="1. Conectar Banco SQL", command=self.acao_inicializar_banco, fg_color="#2b2b2b")
        self.btn_init_db.pack(side="left", padx=15, pady=10)
        self.lbl_status_db = ctk.CTkLabel(self, text="Status: Aguardando", text_color="gray")
        self.lbl_status_db.pack(anchor="w", padx=35)

        self.frame_ingestao = ctk.CTkFrame(self)
        self.frame_ingestao.pack(pady=5, padx=20, fill="x")
        self.btn_carregar_csv = ctk.CTkButton(self.frame_ingestao, text="2. Importar Planilha", command=self.acao_carregar_planilha, state="disabled")
        self.btn_carregar_csv.pack(side="left", padx=15, pady=10)
        self.lbl_status_csv = ctk.CTkLabel(self, text="Mailing: Aguardando", text_color="gray")
        self.lbl_status_csv.pack(anchor="w", padx=35)

        self.btn_disparar_3c = ctk.CTkButton(self, text="🛰️ INJETAR BASE DIRECT API", font=ctk.CTkFont(size=13, weight="bold"), height=45, state="disabled", fg_color="#1b5e20", command=self.processar_esteira_3c)
        self.btn_disparar_3c.pack(pady=15, padx=40, fill="x")

        self.txt_log = ctk.CTkTextbox(self, height=120, activate_scrollbars=True)
        self.txt_log.pack(pady=10, padx=20, fill="x")
        self.escrever_log("Sistema pronto. Alinhamento API Concluído.")
        
        # Garante a inicialização segura com texto limpo
        self.lbl_num_total.configure(text="0")

if __name__ == "__main__":
    app = SoftwareControlDesk()
    app.mainloop()
