import customtkinter as ctk
import os
import sys
import pandas as pd
from tkinter import filedialog

sys.path.append(os.path.dirname(__file__))
import gerenciador_banco
import integrador_3c

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")


class SoftwareControlDesk(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Aex Telecom - Inteligência de Mailings v1.4")
        self.geometry("760x880")
        self.resizable(False, False)

        self.sincronizacao_automatica_ativa = False
        self._job_sincronizacao = None

        # CABEÇALHO
        self.label_titulo = ctk.CTkLabel(self, text="ESTEIRA DE HIGIENIZAÇÃO E CARGA DIRECT API (3C PLUS)", font=ctk.CTkFont(size=18, weight="bold"))
        self.label_titulo.pack(pady=10)

        # DASHBOARD
        self.frame_dash = ctk.CTkFrame(self)
        self.frame_dash.pack(pady=5, padx=20, fill="x")

        self.card_total = ctk.CTkFrame(self.frame_dash, width=160, height=60, fg_color="#1f538d")
        self.card_total.pack(side="left", padx=10, pady=10, expand=True, fill="both")
        self.lbl_num_total = ctk.CTkLabel(self.card_total, text="0", font=ctk.CTkFont(size=18, weight="bold"))
        self.lbl_num_total.pack(pady=(5, 0))
        ctk.CTkLabel(self.card_total, text="Leads no Banco SQL", font=ctk.CTkFont(size=11)).pack()

        self.card_pendentes = ctk.CTkFrame(self.frame_dash, width=160, height=60, fg_color="#8d6d1f")
        self.card_pendentes.pack(side="left", padx=10, pady=10, expand=True, fill="both")
        self.lbl_num_pendentes = ctk.CTkLabel(self.card_pendentes, text="0", font=ctk.CTkFont(size=18, weight="bold"))
        self.lbl_num_pendentes.pack(pady=(5, 0))
        ctk.CTkLabel(self.card_pendentes, text="Pendentes de Envio", font=ctk.CTkFont(size=11)).pack()

        self.card_enviados = ctk.CTkFrame(self.frame_dash, width=160, height=60, fg_color="#1f8d4a")
        self.card_enviados.pack(side="left", padx=10, pady=10, expand=True, fill="both")
        self.lbl_num_enviados = ctk.CTkLabel(self.card_enviados, text="0", font=ctk.CTkFont(size=18, weight="bold"))
        self.lbl_num_enviados.pack(pady=(5, 0))
        ctk.CTkLabel(self.card_enviados, text="Já Enviados à 3C", font=ctk.CTkFont(size=11)).pack()

        # CONFIGURAÇÕES CREDENCIAIS
        self.frame_credenciais = ctk.CTkFrame(self)
        self.frame_credenciais.pack(pady=5, padx=20, fill="x")
        ctk.CTkLabel(self.frame_credenciais, text="Token de API 3C Plus:", font=ctk.CTkFont(size=11, weight="bold")).grid(row=0, column=0, padx=15, pady=10, sticky="w")
        self.txt_api_key = ctk.CTkEntry(self.frame_credenciais, placeholder_text="Cole o token longo da 3C Plus aqui...", width=455, show="*")
        self.txt_api_key.grid(row=0, column=1, padx=5, pady=10)

        ctk.CTkLabel(self.frame_credenciais, text="ID da Campanha 3C:", font=ctk.CTkFont(size=11, weight="bold")).grid(row=1, column=0, padx=15, pady=(0, 10), sticky="w")
        self.txt_campaign_id = ctk.CTkEntry(self.frame_credenciais, placeholder_text="Ex: 1234", width=455)
        self.txt_campaign_id.grid(row=1, column=1, padx=5, pady=(0, 10))

        # BOTOES ETAPAS - BANCO
        self.frame_banco = ctk.CTkFrame(self)
        self.frame_banco.pack(pady=5, padx=20, fill="x")
        self.btn_init_db = ctk.CTkButton(self.frame_banco, text="1. Conectar Banco SQL", command=self.acao_inicializar_banco, fg_color="#2b2b2b", hover_color="#1f1f1f")
        self.btn_init_db.pack(side="left", padx=15, pady=10)
        self.lbl_status_db = ctk.CTkLabel(self, text="Status do Banco: Não verificado", text_color="gray")
        self.lbl_status_db.pack(anchor="w", padx=35)

        # IMPORTAÇÃO CSV
        self.frame_ingestao = ctk.CTkFrame(self)
        self.frame_ingestao.pack(pady=5, padx=20, fill="x")
        self.btn_carregar_csv = ctk.CTkButton(self.frame_ingestao, text="2. Importar Planilha Higienizada", command=self.acao_carregar_planilha, state="disabled", fg_color="#1f538d", hover_color="#14375e")
        self.btn_carregar_csv.pack(side="left", padx=15, pady=10)
        self.lbl_status_csv = ctk.CTkLabel(self, text="Mailing: Aguardando arquivo", text_color="gray")
        self.lbl_status_csv.pack(anchor="w", padx=35)

        # ENVIO PARA 3C: escolha de lista nova ou existente
        self.frame_envio = ctk.CTkFrame(self)
        self.frame_envio.pack(pady=5, padx=20, fill="x")
        ctk.CTkLabel(self.frame_envio, text="3. Envio para a 3C Plus", font=ctk.CTkFont(size=13, weight="bold")).grid(row=0, column=0, columnspan=2, padx=15, pady=(10, 5), sticky="w")

        self.modo_lista = ctk.CTkSegmentedButton(self.frame_envio, values=["Criar Nova Lista", "Usar Lista Existente"], command=self._alternar_modo_lista)
        self.modo_lista.set("Criar Nova Lista")
        self.modo_lista.grid(row=1, column=0, columnspan=2, padx=15, pady=5, sticky="w")

        ctk.CTkLabel(self.frame_envio, text="Nome da nova lista:").grid(row=2, column=0, padx=15, pady=5, sticky="w")
        self.txt_nome_lista = ctk.CTkEntry(self.frame_envio, placeholder_text="Ex: Base RJ - Lote 01", width=300)
        self.txt_nome_lista.grid(row=2, column=1, padx=5, pady=5, sticky="w")

        ctk.CTkLabel(self.frame_envio, text="ID da lista existente:").grid(row=3, column=0, padx=15, pady=5, sticky="w")
        self.txt_id_lista_existente = ctk.CTkEntry(self.frame_envio, placeholder_text="Ex: 5678", width=300, state="disabled")
        self.txt_id_lista_existente.grid(row=3, column=1, padx=5, pady=5, sticky="w")

        ctk.CTkLabel(self.frame_envio, text="Quantidade de leads pendentes a enviar:").grid(row=4, column=0, padx=15, pady=(5, 10), sticky="w")
        self.txt_qtd_lote = ctk.CTkEntry(self.frame_envio, placeholder_text="Ex: 5000", width=300)
        self.txt_qtd_lote.grid(row=4, column=1, padx=5, pady=(5, 10), sticky="w")

        self.btn_disparar_3c = ctk.CTkButton(
            self, text="🛰️ ENVIAR LEADS PENDENTES PARA A 3C (DIRECT API)",
            font=ctk.CTkFont(size=13, weight="bold"), height=45, state="disabled",
            fg_color="#1b5e20", hover_color="#0d3c11", command=self.processar_esteira_3c
        )
        self.btn_disparar_3c.pack(pady=10, padx=40, fill="x")

        # TABULAÇÕES
        self.frame_tabulacao = ctk.CTkFrame(self)
        self.frame_tabulacao.pack(pady=5, padx=20, fill="x")
        ctk.CTkLabel(self.frame_tabulacao, text="4. Tabulações (histórico de ligações)", font=ctk.CTkFont(size=13, weight="bold")).grid(row=0, column=0, columnspan=3, padx=15, pady=(10, 5), sticky="w")

        ctk.CTkLabel(self.frame_tabulacao, text="Sincronizar a cada (minutos):").grid(row=1, column=0, padx=15, pady=10, sticky="w")
        self.txt_intervalo_min = ctk.CTkEntry(self.frame_tabulacao, placeholder_text="15", width=80)
        self.txt_intervalo_min.insert(0, "15")
        self.txt_intervalo_min.grid(row=1, column=1, padx=5, pady=10, sticky="w")

        self.btn_toggle_auto = ctk.CTkButton(self.frame_tabulacao, text="▶ Ativar Sincronização Automática", command=self.alternar_sincronizacao_automatica, fg_color="#5e1b5e", hover_color="#3c0d3c")
        self.btn_toggle_auto.grid(row=1, column=2, padx=15, pady=10, sticky="w")

        self.btn_sync_manual = ctk.CTkButton(self.frame_tabulacao, text="🔄 Sincronizar Agora", command=self.acao_sincronizar_tabulacoes, fg_color="#2b2b2b", hover_color="#1f1f1f")
        self.btn_sync_manual.grid(row=2, column=0, columnspan=1, padx=15, pady=(0, 10), sticky="w")

        self.lbl_status_sync = ctk.CTkLabel(self.frame_tabulacao, text="Sincronização automática: desligada", text_color="gray")
        self.lbl_status_sync.grid(row=2, column=1, columnspan=2, padx=5, pady=(0, 10), sticky="w")

        # LOGS
        self.txt_log = ctk.CTkTextbox(self, height=150, activate_scrollbars=True)
        self.txt_log.pack(pady=10, padx=20, fill="x")
        self.escrever_log("Sistema pronto. Alinhamento Direct API Concluído.")
        self.atualizar_dashboard()

        self.protocol("WM_DELETE_WINDOW", self._ao_fechar)

    # ------------------------------------------------------------------
    # UTILIDADES
    # ------------------------------------------------------------------

    def escrever_log(self, texto):
        self.txt_log.configure(state="normal")
        self.txt_log.insert("end", f" -> {texto}\n")
        self.txt_log.configure(state="disabled")
        self.txt_log.see("end")
        self.update()

    def atualizar_dashboard(self):
        try:
            status = gerenciador_banco.contar_leads_por_status()
            total = sum(status.values())
            pendentes = status.get("pendente", 0) + status.get(None, 0)
            enviados = status.get("enviado", 0)
            self.lbl_num_total.configure(text=str(total))
            self.lbl_num_pendentes.configure(text=str(pendentes))
            self.lbl_num_enviados.configure(text=str(enviados))
        except Exception:
            pass

    def _alternar_modo_lista(self, valor):
        if valor == "Usar Lista Existente":
            self.txt_id_lista_existente.configure(state="normal")
            self.txt_nome_lista.configure(state="disabled")
        else:
            self.txt_id_lista_existente.configure(state="disabled")
            self.txt_nome_lista.configure(state="normal")

    def _ao_fechar(self):
        if self._job_sincronizacao is not None:
            self.after_cancel(self._job_sincronizacao)
        self.destroy()

    # ------------------------------------------------------------------
    # ETAPA 1: BANCO
    # ------------------------------------------------------------------

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

    # ------------------------------------------------------------------
    # ETAPA 2: IMPORTAÇÃO DE PLANILHA
    # ------------------------------------------------------------------

    def acao_carregar_planilha(self):
        caminho_arquivo = filedialog.askopenfilename(title="Selecione o arquivo", filetypes=[("CSV", "*.csv")])
        if not caminho_arquivo:
            return

        self.escrever_log("Lendo base cadastral...")
        try:
            df = pd.read_csv(caminho_arquivo, dtype=str, sep=';')
            self.escrever_log(f"[DEBUG] Colunas lidas no arquivo: {list(df.columns)[:5]}...")

            df_para_banco = pd.DataFrame()
            df_para_banco['cnpj'] = df['cnpj'].str.strip().str.zfill(14)
            df_para_banco['nome_empresa'] = df['razao_social'].str.strip()
            df_para_banco['celular_original'] = df['celular_1'].str.strip() if 'celular_1' in df.columns else df[df.columns[-2]].str.strip()
            df_para_banco['operadora'] = df.iloc[:, -1].str.strip().str.upper()

            logr = df['logradouro'] if 'logradouro' in df.columns else ''
            num = df['numero'] if 'numero' in df.columns else ''
            bairro = df['bairro'] if 'bairro' in df.columns else ''
            cidade = df['municipio'] if 'municipio' in df.columns else ''
            uf = df['uf'] if 'uf' in df.columns else 'RJ'
            df_para_banco['cep'] = df['cep'] if 'cep' in df.columns else '00000-000'
            df_para_banco['endereco_completo'] = logr + ", " + num + " - " + bairro + ", " + cidade + "/" + uf

            # Remove duplicados dentro da própria planilha
            df_para_banco = df_para_banco.drop_duplicates(subset=['cnpj'], keep='first')

            # Evita reimportar CNPJs que já existem no banco (novos leads apenas)
            conn = gerenciador_banco.conectar_banco()
            cnpjs_existentes = set(pd.read_sql("SELECT cnpj FROM mailing_corporativo", conn)['cnpj'])
            antes = len(df_para_banco)
            df_para_banco = df_para_banco[~df_para_banco['cnpj'].isin(cnpjs_existentes)]
            duplicados_ignorados = antes - len(df_para_banco)

            if len(df_para_banco) > 0:
                df_para_banco.to_sql('mailing_corporativo', conn, if_exists='append', index=False)
                conn.commit()
            conn.close()

            self.lbl_status_csv.configure(text=f"Mailing: {len(df_para_banco)} leads novos prontos", text_color="green")
            self.atualizar_dashboard()
            self.escrever_log(f"[SUCESSO] {len(df_para_banco)} leads novos carregados no SQL "
                               f"({duplicados_ignorados} já existiam no banco e foram ignorados).")

        except Exception as erro_real:
            causa_interna = erro_real.__cause__ if erro_real.__cause__ else erro_real
            self.escrever_log(f"[ERRO DE CARGA REAL] Causa no SQLite: {causa_interna}")

    # ------------------------------------------------------------------
    # ETAPA 3: ENVIO PARA A 3C (lista nova ou existente)
    # ------------------------------------------------------------------

    def processar_esteira_3c(self):
        token = self.txt_api_key.get().strip()
        if not token:
            self.escrever_log("ERRO: Cole o Token de API da 3C Plus antes de avançar!")
            return

        id_campanha = self.txt_campaign_id.get().strip()
        if not id_campanha:
            self.escrever_log("ERRO: Informe o ID da Campanha 3C.")
            return

        qtd_lote = self.txt_qtd_lote.get().strip()
        if not qtd_lote or not qtd_lote.isdigit():
            self.escrever_log("ERRO: Informe uma quantidade válida de leads a enviar.")
            return

        self.escrever_log(f"Buscando até {qtd_lote} leads PENDENTES no banco local...")
        leads = gerenciador_banco.buscar_leads_pendentes(int(qtd_lote))
        if not leads:
            self.escrever_log("AVISO: Não há leads pendentes de envio no banco local!")
            return

        modo = self.modo_lista.get()
        try:
            if modo == "Usar Lista Existente":
                id_lista = self.txt_id_lista_existente.get().strip()
                if not id_lista:
                    self.escrever_log("ERRO: Informe o ID da lista existente na 3C.")
                    return
                resumo = integrador_3c.enviar_lote_lista_existente(token, id_campanha, id_lista, leads, log_callback=self.escrever_log)
            else:
                nome_lista = self.txt_nome_lista.get().strip() or f"Base - Lote {qtd_lote}"
                resumo = integrador_3c.enviar_lote_nova_lista(token, id_campanha, nome_lista, leads, log_callback=self.escrever_log)

            gerenciador_banco.marcar_leads_enviados(resumo["cnpjs_enviados"], resumo["id_lista"], id_campanha)

            self.escrever_log(f"[SUCESSO] {resumo['importados']} contatos importados na lista {resumo['id_lista']}.")
            if resumo["filtrados"]:
                self.escrever_log(f"[ATENÇÃO] {len(resumo['filtrados'])} contatos filtrados/rejeitados pela 3C.")
                for item in resumo["filtrados"][:10]:
                    motivo = item.get("motive", "Motivo desconhecido") if isinstance(item, dict) else str(item)
                    self.escrever_log(f"   -> Rejeitado: {motivo}")

            self.atualizar_dashboard()

        except integrador_3c.ErroIntegracao3C as e:
            self.escrever_log(f"[ERRO 3C] {e}")
        except Exception as e:
            self.escrever_log(f"[ERRO INESPERADO] {e}")

    # ------------------------------------------------------------------
    # ETAPA 4: TABULAÇÕES
    # ------------------------------------------------------------------

    def acao_sincronizar_tabulacoes(self):
        token = self.txt_api_key.get().strip()
        id_campanha = self.txt_campaign_id.get().strip()
        if not token or not id_campanha:
            self.escrever_log("ERRO: Preencha Token e ID da Campanha antes de sincronizar tabulações.")
            return

        self.escrever_log("Sincronizando tabulações com a 3C Plus...")
        try:
            atualizados, sem_match = integrador_3c.sincronizar_tabulacoes(
                token, id_campanha, gerenciador_banco, log_callback=self.escrever_log
            )
            if atualizados == 0 and sem_match == 0:
                self.escrever_log("Nenhuma chamada retornada pela 3C para esta campanha ainda.")
        except integrador_3c.ErroIntegracao3C as e:
            self.escrever_log(f"[ERRO 3C] {e}")
        except Exception as e:
            self.escrever_log(f"[ERRO INESPERADO] {e}")

    def alternar_sincronizacao_automatica(self):
        if self.sincronizacao_automatica_ativa:
            if self._job_sincronizacao is not None:
                self.after_cancel(self._job_sincronizacao)
                self._job_sincronizacao = None
            self.sincronizacao_automatica_ativa = False
            self.btn_toggle_auto.configure(text="▶ Ativar Sincronização Automática", fg_color="#5e1b5e", hover_color="#3c0d3c")
            self.lbl_status_sync.configure(text="Sincronização automática: desligada", text_color="gray")
            self.escrever_log("Sincronização automática de tabulações DESLIGADA.")
        else:
            intervalo_texto = self.txt_intervalo_min.get().strip()
            if not intervalo_texto or not intervalo_texto.isdigit() or int(intervalo_texto) <= 0:
                self.escrever_log("ERRO: Informe um intervalo válido em minutos (número inteiro maior que zero).")
                return
            self.sincronizacao_automatica_ativa = True
            self.btn_toggle_auto.configure(text="⏸ Desativar Sincronização Automática", fg_color="#8d1f1f", hover_color="#5e1414")
            self.lbl_status_sync.configure(text=f"Sincronização automática: ativa (a cada {intervalo_texto} min)", text_color="green")
            self.escrever_log(f"Sincronização automática de tabulações LIGADA (a cada {intervalo_texto} min).")
            self._executar_ciclo_sincronizacao_automatica()

    def _executar_ciclo_sincronizacao_automatica(self):
        if not self.sincronizacao_automatica_ativa:
            return

        self.acao_sincronizar_tabulacoes()

        intervalo_texto = self.txt_intervalo_min.get().strip()
        intervalo_min = int(intervalo_texto) if intervalo_texto.isdigit() and int(intervalo_texto) > 0 else 15
        intervalo_ms = intervalo_min * 60 * 1000
        self._job_sincronizacao = self.after(intervalo_ms, self._executar_ciclo_sincronizacao_automatica)


if __name__ == "__main__":
    app = SoftwareControlDesk()
    app.mainloop()
