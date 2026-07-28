import customtkinter as ctk
import os
import sys
import pandas as pd
from tkinter import filedialog

sys.path.append(os.path.dirname(__file__))
import gerenciador_banco
import motores

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class SoftwareControlDesk(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Aex Telecom - Inteligência de Mailings v1.1")
        self.geometry("720x680")
        self.resizable(False, False)

        # CABEÇALHO
        self.label_titulo = ctk.CTkLabel(self, text="ESTEIRA DE HIGIENIZAÇÃO INTELIGENTE", font=ctk.CTkFont(size=20, weight="bold"))
        self.label_titulo.pack(pady=10)

        # DASHBOARD
        self.frame_dash = ctk.CTkFrame(self)
        self.frame_dash.pack(pady=5, padx=20, fill="x")

        self.card_total = ctk.CTkFrame(self.frame_dash, width=150, height=60, fg_color="#1f538d")
        self.card_total.pack(side="left", padx=10, pady=10, expand=True, fill="both")
        self.lbl_num_total = ctk.CTkLabel(self.card_total, text="0", font=ctk.CTkFont(size=18, weight="bold"))
        self.lbl_num_total.pack(pady=(5,0))
        ctk.CTkLabel(self.card_total, text="Total no Banco", font=ctk.CTkFont(size=11)).pack()

        self.card_aprovados = ctk.CTkFrame(self.frame_dash, width=150, height=60, fg_color="#2e7d32")
        self.card_aprovados.pack(side="left", padx=10, pady=10, expand=True, fill="both")
        self.lbl_num_aprovados = ctk.CTkLabel(self.card_aprovados, text="0", font=ctk.CTkFont(size=18, weight="bold"))
        self.lbl_num_aprovados.pack(pady=(5,0))
        ctk.CTkLabel(self.card_aprovados, text="Aprovados B2B", font=ctk.CTkFont(size=11)).pack()

        self.card_expurgados = ctk.CTkFrame(self.frame_dash, width=150, height=60, fg_color="#c62828")
        self.card_expurgados.pack(side="left", padx=10, pady=10, expand=True, fill="both")
        self.lbl_num_expurgados = ctk.CTkLabel(self.card_expurgados, text="0", font=ctk.CTkFont(size=18, weight="bold"))
        self.lbl_num_expurgados.pack(pady=(5,0))
        ctk.CTkLabel(self.card_expurgados, text="Leads Ociosos", font=ctk.CTkFont(size=11)).pack()

        # CONFIGURAÇÕES CREDENCIAIS
        self.frame_credenciais = ctk.CTkFrame(self)
        self.frame_credenciais.pack(pady=5, padx=20, fill="x")
        ctk.CTkLabel(self.frame_credenciais, text="Chave de API / Token Credilink:", font=ctk.CTkFont(size=11, weight="bold")).grid(row=0, column=0, padx=15, pady=5, sticky="w")
        self.txt_api_key = ctk.CTkEntry(self.frame_credenciais, placeholder_text="Cole o Token da API aqui se liberado...", width=420, show="*")
        self.txt_api_key.grid(row=0, column=1, padx=5, pady=5)

        # INFRAESTRUTURA BANCO
        self.frame_banco = ctk.CTkFrame(self)
        self.frame_banco.pack(pady=5, padx=20, fill="x")
        self.btn_init_db = ctk.CTkButton(self.frame_banco, text="1. Inicializar Banco SQL", command=self.acao_inicializar_banco, fg_color="#2b2b2b", hover_color="#1f1f1f")
        self.btn_init_db.pack(side="left", padx=15, pady=10)
        self.lbl_status_db = ctk.CTkLabel(self, text="Status do Banco: Não verificado", text_color="gray")
        self.lbl_status_db.pack(anchor="w", padx=35)

        # IMPORTAÇÃO PLANILHA
        self.frame_ingestao = ctk.CTkFrame(self)
        self.frame_ingestao.pack(pady=5, padx=20, fill="x")
        self.btn_carregar_csv = ctk.CTkButton(self.frame_ingestao, text="2. Importar Planilha Bruta", command=self.acao_carregar_planilha, state="disabled", fg_color="#1f538d", hover_color="#14375e")
        self.btn_carregar_csv.pack(side="left", padx=15, pady=10)
        self.lbl_status_csv = ctk.CTkLabel(self, text="Mailing: Nenhum arquivo no SQL", text_color="gray")
        self.lbl_status_csv.pack(anchor="w", padx=35)

        # CONTROLES OPERACIONAIS
        self.btn_esteira_receita = ctk.CTkButton(self, text="🚀 DISPARAR ESTEIRA 1: FILTRO CRONOLÓGICO RECEITA", font=ctk.CTkFont(size=13, weight="bold"), height=40, state="disabled", command=self.disparar_motor_receita)
        self.btn_esteira_receita.pack(pady=8, padx=40, fill="x")

        self.btn_esteira_credilink = ctk.CTkButton(self, text="🔍 DISPARAR ESTEIRA 2: ENRIQUECEDOR EM LOTE (API/ROBÔ)", font=ctk.CTkFont(size=13, weight="bold"), height=40, state="disabled", fg_color="#8B0000", hover_color="#5A0000", command=self.disparar_motor_credilink)
        self.btn_esteira_credilink.pack(pady=8, padx=40, fill="x")

        # CONSOLE DE LOGS
        self.txt_log = ctk.CTkTextbox(self, height=110, activate_scrollbars=True)
        self.txt_log.pack(pady=10, padx=20, fill="x")
        self.escrever_log("Sistema pronto. Painel de métricas ativado.")
        
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
            total = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM mailing_corporativo WHERE status_receita = 'APROVADO'")
            aprovados = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM mailing_corporativo WHERE status_receita LIKE 'EXPURGAR%'")
            expurgados = cursor.fetchone()[0]
            conn.close()
            
            self.lbl_num_total.configure(text=str(total))
            self.lbl_num_aprovados.configure(text=str(aprovados))
            self.lbl_num_expurgados.configure(text=str(expurgados))
        except:
            pass

    def acao_inicializar_banco(self):
        try:
            gerenciador_banco.inicializar_tabelas()
            self.lbl_status_db.configure(text="Status do Banco: SQLITE3 ATIVO E CONECTADO", text_color="green")
            self.btn_carregar_csv.configure(state="normal")
            self.atualizar_dashboard()
            self.escrever_log("Banco de dados relacional e infraestrutura de KPIs ativos.")
        except Exception as e:
            self.escrever_log(f"Falha de Infraestrutura: {e}")

    def acao_carregar_planilha(self):
        caminho_arquivo = filedialog.askopenfilename(title="Selecione o arquivo de mailing bruto", filetypes=[("Arquivos CSV", "*.csv")])
        if caminho_arquivo:
            self.escrever_log(f"Lendo base cadastral: {os.path.basename(caminho_arquivo)}...")
            try:
                df = pd.read_csv(caminho_arquivo, dtype=str, sep=None, engine='python')
                total = len(df)
                self.escrever_log(f"Carregados {total} leads na memória RAM. Migrando para o SQL...")

                col_cnpj = 'cnpj' if 'cnpj' in df.columns else df.columns
                col_nome = 'nome' if 'nome' in df.columns else (df.columns if len(df.columns) > 1 else '')
                col_tel = 'celular_1' if 'celular_1' in df.columns else df.columns[-1]
                col_ope = 'operadora' if 'operadora' in df.columns else ''

                for _, row in df.iterrows():
                    gerenciador_banco.salvar_lead_bruto(str(row.get(col_cnpj, '')), str(row.get(col_nome, '')), str(row.get(col_tel, '')), str(row.get(col_ope, '')))
                
                self.lbl_status_csv.configure(text=f"Mailing: Base importada com {total} leads", text_color="green")
                self.btn_esteira_receita.configure(state="normal")
                self.btn_esteira_credilink.configure(state="normal")
                self.atualizar_dashboard()
                self.escrever_log("[SUCESSO] Ingestão concluída! O Dashboard foi atualizado.")
            except Exception as e:
                self.escrever_log(f"Erro na carga do CSV: {e}")

    def disparar_motor_receita(self):
        motores.executar_esteira_receita(self)

    def disparar_motor_credilink(self):
        token = self.txt_api_key.get().strip()
        motores.executar_esteira_credilink(self, token_api=token if token else None)

if __name__ == "__main__":
    app = SoftwareControlDesk()
    app.mainloop()
