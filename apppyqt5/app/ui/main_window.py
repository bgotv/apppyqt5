"""
main_window
Módulo de interface gráfica - Janela principal da aplicação.
Versão corrigida para aceitar os parâmetros do main_corrected.py.
"""

import pandas as pd
import time
from app.utils.logger import metrics_manager
from app.utils.status_calculator import calcular_tipo_projeto
from PyQt5.QtWidgets import QFileDialog
import csv
import os, sqlite3, json, shutil
from PyQt5.QtWidgets import (
    QMainWindow, QTabWidget, QWidget, QVBoxLayout,
    QHBoxLayout, QLabel, QPushButton, QMessageBox, QStatusBar,
    QSplitter, QTreeWidget, QTreeWidgetItem, QHeaderView, QComboBox, QGroupBox

)
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt5.QtGui import QFont
from app.config import settings
from app.ui.analysis_form_corrected import AnalysisForm
from app.ui.results_view import ResultsView
from app.ui.flags_view import FlagsView
from app.ui.notes_lock_view import NotesTreeView, NotesLockPanel
from app.utils.logger import log_ui_action
from app.utils.performance import PerformanceTracker
from PyQt5.QtCore import Qt, pyqtSlot
from datetime import datetime, timedelta
# from app.ui.filters_integration import adicionar_filtros_a_main_window
# from PyQt5.QtChart import (
#     QChart, QChartView, QPieSeries,
#     QBarSeries, QBarSet, QBarCategoryAxis, QValueAxis
# )
from app.ui.gestao_view import GestaoView
from app.automation.web_automation import abrir_atividade  
from app.utils.email_sender import build_email_html, enviar_email_power_automate_html
from app.config.settings import POWER_AUTOMATE_URL, REMETENTE_FIXO
from PyQt5.QtWidgets import (
    QVBoxLayout, QTreeWidget, QTreeWidgetItem, QSizePolicy
)
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from app.utils.logger import metrics_manager
from collections import defaultdict
import getpass






class MainWindow(QMainWindow):
    """
    Janela principal da aplicação.
    """
    
    def __init__(self, flags_manager=None, lock_manager=None, decision_tree=None, 
                 report_generator=None, web_automation=None):
        """
        Inicializa a janela principal.
        
        Args:
            flags_manager: Gerenciador de flags.
            lock_manager: Gerenciador de bloqueio de notas.
            decision_tree: Árvore de decisão.
            report_generator: Gerador de pareceres.
            web_automation: Gerenciador de automação web.
        """
        super().__init__()
        
        # Componentes do sistema
        self.flags_manager = flags_manager
        self.lock_manager = lock_manager
        self.decision_tree = decision_tree
        self.report_generator = report_generator
        self.web_automation = web_automation
        
        # Configurações da janela
        self.setWindowTitle(f"{settings.APP_NAME} v{settings.APP_VERSION}")
        self.setMinimumSize(600, 400)
        
        # Inicializa a interface
        self._init_ui()
        
        # Registra a inicialização
        log_ui_action('main_window_initialized')
    
    def _init_ui(self):
        """Inicializa os componentes da interface."""
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal
        main_layout = QVBoxLayout(central_widget)
        
        # Barra de status
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Pronto")
        
        # Tabs para navegação entre etapas
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)
        
        # Tab de consulta de notas
        self.tab_consulta = QWidget()
        self.tabs.addTab(self.tab_consulta, "Consulta de Notas")
        
        # Tab de análise
        self.tab_analise = QWidget()
        self.tabs.addTab(self.tab_analise, "Análise Técnica")
        
        # Tab de resultados
        self.tab_resultados = QWidget()
        self.tabs.addTab(self.tab_resultados, "Resultados")
        
        # Tab de métricas de desempenho
        self.tab_metricas = QWidget()
        self.tabs.addTab(self.tab_metricas, "Métricas")
        
        # --- aba de Gestão (visão gerencial) ---
        self.tab_gestao = GestaoView(parent=self)
        self.tabs.addTab(self.tab_gestao, "Gestão")
        
        # Inicializa o conteúdo de cada tab
        self._init_tab_consulta()
        self._init_tab_analise()
        self._init_tab_resultados()
        self._init_tab_metricas()
        self._init_sync_db()
        
        # Conecta eventos
        self.tabs.currentChanged.connect(self._on_tab_changed)
        
        
    def _init_sync_db(self):
        os.makedirs(settings.NETWORK_ROOT, exist_ok=True)
        conn = sqlite3.connect(settings.DB_PATH)
        c = conn.cursor()
        c.execute("""
        CREATE TABLE IF NOT EXISTS sync_records (
        nr_atividade TEXT PRIMARY KEY,
        cd_projeto   TEXT,
        valores_site TEXT,
        arquivos     TEXT,
        file_sizes   TEXT,
        last_sync    TEXT,
        status       TEXT
        )""")
        conn.commit()
        conn.close()
    
    # verificar se existe o download na pasta da rede e se não houver fazer o download novamente    
    def _ensure_downloaded(self,
                           nr_atividade: str,
                           cd_projeto: str,
                           skip_move: bool = False
                           ) -> tuple[str, dict]:
        """
        Garante que exista um download íntegro para nr_atividade.
        Se já houver registro e todos os arquivos em NETWORK_ROOT/<nr_atividade>
        tiverem tamanho correto, retorna (dest, valores_site).
        Senão, chama abrir_atividade(); se skip_move=False, move para
        NETWORK_ROOT/<nr_atividade>, senão mantém em pasta temporária de Downloads.
        Persiste no SQLite o JSON de valores_site, lista de arquivos e seus tamanhos.
        Retorna (folder_para_ui, valores_site).
        """
        dest = os.path.join(settings.NETWORK_ROOT, nr_atividade)

        # 1) Tenta ler do SQLite
        conn = sqlite3.connect(settings.DB_PATH)
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS sync_records (
                nr_atividade TEXT PRIMARY KEY,
                cd_projeto   TEXT,
                valores_site TEXT,
                arquivos     TEXT,
                file_sizes   TEXT,
                last_sync    TEXT,
                status       TEXT
            )
        """)
        conn.commit()

        c.execute(
            "SELECT valores_site, arquivos, file_sizes FROM sync_records WHERE nr_atividade=?",
            (nr_atividade,)
        )
        row = c.fetchone()
        conn.close()

        # 2) Se já existe em rede e registro, valida tamanhos
        if row and os.path.isdir(dest):
            vs_json, arquivos_json, sizes_json = row
            file_sizes = json.loads(sizes_json)
            all_good = True
            for fname, expected in file_sizes.items():
                p = os.path.join(dest, fname)
                if not os.path.isfile(p) or os.path.getsize(p) != expected:
                    all_good = False
                    break
            if all_good:
                return dest, json.loads(vs_json)

        # 3) Senão: fresh download
        downloads_folder, valores_site = abrir_atividade(nr_atividade, cd_projeto)

        # decide onde ficará a pasta para a UI
        if not skip_move:
            # remove antiga e move nova para a rede
            if os.path.isdir(dest):
                shutil.rmtree(dest)
            shutil.move(downloads_folder, dest)
            folder_para_ui = dest
        else:
            # deixa no downloads local
            folder_para_ui = downloads_folder

        # 4) Reconstrói lista de arquivos e tamanhos a partir da pasta escolhida
        arquivos = sorted(os.listdir(folder_para_ui))
        file_sizes = {
            f: os.path.getsize(os.path.join(folder_para_ui, f))
            for f in arquivos
        }

        # 5) Persiste no SQLite (valores_site, lista e tamanhos)
        conn = sqlite3.connect(settings.DB_PATH)
        c = conn.cursor()
        c.execute("""
            INSERT OR REPLACE INTO sync_records
              (nr_atividade, cd_projeto, valores_site, arquivos, file_sizes, last_sync, status)
            VALUES (?,?,?,?,?,?,?)
        """, (
            nr_atividade,
            cd_projeto,
            json.dumps(valores_site, ensure_ascii=False),
            json.dumps(arquivos,     ensure_ascii=False),
            json.dumps(file_sizes,   ensure_ascii=False),
            time.strftime("%Y-%m-%d %H:%M:%S"),
            "OK"
        ))
        conn.commit()
        conn.close()

        return folder_para_ui, valores_site

        
    def _apply_filters(self):
        """Filtra self.all_notes pelos controles e popula a tree."""
        from app.utils.status_calculator import calcular_status

        base = getattr(self, 'all_notes', [])
        num  = self.filtro_entry.text().strip()
        status = self.status_combobox.currentText().strip().upper()
        com  = self.filtro_com_combobox.currentText().strip().lower()
        tec  = self.filtro_tec_combobox.currentText().strip().lower()
        resp = self.filtro_resp_combobox.currentText().strip().lower()
        inicio = self.data_inicio.date().toPyDate()
        fim    = self.data_fim.date().toPyDate()

        filtradas = []
        import re
        for note in base:
            # número
            n_str = str(note.get("NR_ATIVIDADE",""))
            if num and num not in n_str:
                continue

            # status
            stat = calcular_status(note.get("DT_CADASTRO",""))
            if status and status != "TODOS":
                if status == "D7+":
                    m = re.match(r'^D(\d+)\+?$', stat)
                    if not (m and int(m.group(1)) >= 7):
                        continue
                else:
                    if stat != status:
                        continue

            # comercial / técnica / resp.
            if com and str(note.get("AGUARDA_ANALISE_COMERCIAL","")).lower() != com:
                continue
            if tec and str(note.get("AGUARDA_ANALISE_TECNICA","")).lower() != tec:
                continue
            if resp and str(note.get("PROJ_RESP","")).lower() != resp:
                continue
                    # **novo filtro: tipo de projeto**
            tipo_sel = self.filtro_tipo_projeto.currentText().strip()
            if tipo_sel and tipo_sel != "Todos":
                if note.get("TIPO_PROJETO", "") != tipo_sel:
                    continue

            # período
            from datetime import datetime
            try:
                cad = datetime.strptime(note.get("DT_CADASTRO",""), "%d-%m-%y").date()
            except:
                continue
            if not (inicio <= cad <= fim):
                continue

            filtradas.append(note)

        # # popula a árvore
        self.filtered_notes = filtradas
        self.tree_notas.set_notes(self.filtered_notes)
        if hasattr(self, 'tab_gestao'):
            self.tab_gestao.set_notes_data(self.filtered_notes)
    
    def _init_tab_consulta(self):
        """Inicializa a tab de consulta de notas, com filtros e árvore ordenável."""
        from PyQt5.QtWidgets import (
            QFrame, QLineEdit, QComboBox, QDateEdit, QLabel, QHBoxLayout, QVBoxLayout
        )
        from PyQt5.QtCore import QDate

        layout = QVBoxLayout(self.tab_consulta)
        
        # 1) Título e botões
        title = QLabel("Consulta de Atividades")
        title.setFont(QFont("Arial", 14, QFont.Bold))
        layout.addWidget(title)
        
        btns = QHBoxLayout()
        self.btn_consultar = QPushButton("Consultar Notas")
        self.btn_consultar.clicked.connect(self._on_consultar_clicked)
        btns.addWidget(self.btn_consultar)
        
        self.btn_atualizar = QPushButton("Atualizar")
        self.btn_atualizar.clicked.connect(self._on_atualizar_clicked)  
        btns.addWidget(self.btn_atualizar)
        
        self.btn_exportar_notas = QPushButton("Exportar Notas")
        self.btn_exportar_notas.clicked.connect(self._on_exportar_notas_clicked)
        btns.addWidget(self.btn_exportar_notas)
        btns.addStretch()
        layout.addLayout(btns)
        
        # 2) Filtros
        filtro_frame = QFrame()
        filtro_layout = QHBoxLayout(filtro_frame)
        
        # Número
        filtro_layout.addWidget(QLabel("Número:"))
        self.filtro_entry = QLineEdit()
        self.filtro_entry.setPlaceholderText("parte do nº da atividade")
        filtro_layout.addWidget(self.filtro_entry)
        
        # Status
        filtro_layout.addWidget(QLabel("Status:"))
        self.status_combobox = QComboBox()
        # primeiro item vazio -> "Todos"
        self.status_combobox.addItems(["", "D0","D1","D2","D3","D4","D5","D6","D7+"])
        self.status_combobox.setItemText(0, "Todos")
        filtro_layout.addWidget(self.status_combobox)
        
        # Comercial
        filtro_layout.addWidget(QLabel("Comercial:"))
        self.filtro_com_combobox = QComboBox()
        self.filtro_com_combobox.addItems(["","Sim","Não"])
        filtro_layout.addWidget(self.filtro_com_combobox)
        
        # Técnica
        filtro_layout.addWidget(QLabel("Técnica:"))
        self.filtro_tec_combobox = QComboBox()
        self.filtro_tec_combobox.addItems(["","Sim","Não"])
        filtro_layout.addWidget(self.filtro_tec_combobox)
        
        # Resp. Projeto
        filtro_layout.addWidget(QLabel("Resp. Projeto:"))
        self.filtro_resp_combobox = QComboBox()
        self.filtro_resp_combobox.addItems(["","GA","O&M"])
        filtro_layout.addWidget(self.filtro_resp_combobox)
        
        # Filtro Tipo de Projeto
        filtro_layout.addWidget(QLabel("Tipo Projeto:"))
        self.filtro_tipo_projeto = QComboBox()
        # primeiro item vazio = "Todos"
        self.filtro_tipo_projeto.addItem("Todos")
        # preencha com as opções que você calculou em NotesTreeView.calcular_tipo_projeto
        self.filtro_tipo_projeto.addItems([
            "Novo Projeto", "Reanálise", "No Inbox", "Indefinido"
        ])
        filtro_layout.addWidget(self.filtro_tipo_projeto)
        
        # Período
        filtro_layout.addWidget(QLabel("De:"))
        self.data_inicio = QDateEdit(calendarPopup=True)
        self.data_inicio.setDate(QDate.currentDate().addMonths(-1))
        filtro_layout.addWidget(self.data_inicio)
        filtro_layout.addWidget(QLabel("Até:"))
        self.data_fim = QDateEdit(calendarPopup=True)
        self.data_fim.setDate(QDate.currentDate())
        filtro_layout.addWidget(self.data_fim)
        
        filtro_layout.addStretch()
        layout.addWidget(filtro_frame)
        
        # Conecta todos os sinais de filtro ao mesmo slot
        for w, sig in [
            (self.filtro_entry, 'textChanged'),
            (self.status_combobox, 'currentIndexChanged'),
            (self.filtro_com_combobox, 'currentIndexChanged'),
            (self.filtro_tec_combobox, 'currentIndexChanged'),
            (self.filtro_resp_combobox, 'currentIndexChanged'),
            (self.data_inicio, 'dateChanged'),
            (self.data_fim, 'dateChanged'),
            (self.filtro_tipo_projeto, 'currentIndexChanged'),
        ]:
            getattr(w, sig).connect(self._apply_filters)
        
        # 3) Árvore de notas
        self.tree_notas = NotesTreeView(self.lock_manager)
        self.tree_notas.note_selected.connect(self._on_nota_selected)
        self.tree_notas.setSortingEnabled(True)
        hdr = self.tree_notas.header()
        hdr.setSectionsClickable(True)
        hdr.setSortIndicatorShown(True)
        layout.addWidget(self.tree_notas)
        
        # 4) Painel de bloqueio e avançar
        self.lock_panel = NotesLockPanel(self.tree_notas)
        layout.addWidget(self.lock_panel)
        self.btn_avancar = QPushButton("Avançar para Análise")
        self.btn_avancar.clicked.connect(self._on_avancar_clicked)
        layout.addWidget(self.btn_avancar)
        
    def _init_tab_analise(self):
        """Inicializa a tab de análise técnica."""
        layout = QVBoxLayout(self.tab_analise)
        
        # Título
        title_label = QLabel("Análise Técnica")
        title_label.setFont(QFont("Arial", 14, QFont.Bold))
        layout.addWidget(title_label)
        
        # Splitter para dividir a tela
        splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(splitter)
        
        # Painel esquerdo - Formulário de análise
        self.analysis_form = AnalysisForm(parent=self, lock_manager=self.lock_manager)
        self.analysis_form.question_answered.connect(self._on_question_answered)
        self.analysis_form.analysis_completed.connect(self._on_analysis_completed)
        splitter.addWidget(self.analysis_form)
        
        # Painel direito - Visualização de flags
        self.flags_view = FlagsView()
        splitter.addWidget(self.flags_view)
        self.flags_view.hide()   
        
        # Define proporções iniciais do splitter
        splitter.setSizes([600, 400])
        
        # Botões de ação
        buttons_layout = QHBoxLayout()
        
        self.btn_baixar_anexos = QPushButton("Baixar Anexos")
        self.btn_baixar_anexos.clicked.connect(self._on_baixar_anexos_clicked)
        buttons_layout.addWidget(self.btn_baixar_anexos)
        
        self.btn_limpar_flags = QPushButton("Limpar Flags")
        self.btn_limpar_flags.clicked.connect(self._on_limpar_flags_clicked)
        buttons_layout.addWidget(self.btn_limpar_flags)
        
        buttons_layout.addStretch()
        
        self.btn_gerar_parecer = QPushButton("Gerar Parecer")
        self.btn_gerar_parecer.clicked.connect(self._on_gerar_parecer_clicked)
        buttons_layout.addWidget(self.btn_gerar_parecer)
        
        layout.addLayout(buttons_layout)
    
    def _init_tab_resultados(self):
        """Inicializa a tab de resultados."""
        layout = QVBoxLayout(self.tab_resultados)
        
        # Título
        title_label = QLabel("Resultados e Parecer")
        title_label.setFont(QFont("Arial", 14, QFont.Bold))
        layout.addWidget(title_label)
        
        # Visualização de resultados
        self.results_view = ResultsView()
        layout.addWidget(self.results_view)
        
        # conecta o toggled e o valueChanged
        self.results_view.chk_with_deadline.toggled.connect(self._refresh_report)
        self.results_view.spn_deadline_days.valueChanged.connect(self._refresh_report)
        
        # Botões de ação
        buttons_layout = QHBoxLayout()
        
        self.btn_copiar = QPushButton("Copiar Parecer")
        self.btn_copiar.clicked.connect(self._on_copiar_clicked)
        buttons_layout.addWidget(self.btn_copiar)
        
        self.btn_salvar = QPushButton("Salvar Parecer")
        self.btn_salvar.clicked.connect(self._on_salvar_clicked)
        buttons_layout.addWidget(self.btn_salvar)
        
        buttons_layout.addStretch()
        
        self.btn_enviar_email = QPushButton("Enviar por E-mail")
        self.btn_enviar_email.clicked.connect(self._on_enviar_email_clicked)
        buttons_layout.addWidget(self.btn_enviar_email)
        
        layout.addLayout(buttons_layout)
        

    def _init_tab_metricas(self):
        """Inicializa a aba de Métricas com filtro por mês, JSON e gráficos."""
        layout = QVBoxLayout(self.tab_metricas)
        
        # Título da aba
        title_layout = QHBoxLayout()
        title_label = QLabel("📈 Análise de Performance")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #2c3e50;
                padding: 10px;
            }
        """)
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        layout.addLayout(title_layout)

        # Painel de controles
        controls_group = QGroupBox("🎛️ Controles")
        controls_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #e74c3c;
                border-radius: 5px;
                margin: 5px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        controls_layout = QHBoxLayout(controls_group)
        
        # Filtro de mês
        controls_layout.addWidget(QLabel("📅 Mês:"))
        self.cmb_mes = QComboBox()
        self.cmb_mes.setStyleSheet("""
            QComboBox {
                padding: 5px;
                border: 1px solid #bdc3c7;
                border-radius: 3px;
                min-width: 120px;
            }
        """)
        
        # Popule com os meses a partir dos arquivos Parquet
        pasta = r"\\pfl-cps-file\Divisao_GD\Data\data\performance"
        meses = []
        try:
            for fn in os.listdir(pasta):
                if fn.startswith("stages_") and fn.endswith(".parquet"):
                    # espera formato stages_YYYY_MM.parquet
                    partes = fn.replace(".parquet","").split("_")
                    if len(partes)==3:
                        meses.append(f"{partes[1]}-{partes[2]}")
        except:
            # Se não conseguir acessar a pasta, adiciona mês atual
            from datetime import datetime
            mes_atual = datetime.now().strftime("%Y-%m")
            meses = [mes_atual]
            
        meses = sorted(set(meses))
        self.cmb_mes.addItems(meses)
        self.cmb_mes.currentTextChanged.connect(self._refresh_metrics)
        controls_layout.addWidget(self.cmb_mes)

        # Botão de refresh manual
        btn_refresh = QPushButton("🔄 Atualizar Métricas")
        btn_refresh.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
            QPushButton:pressed {
                background-color: #a93226;
            }
        """)
        btn_refresh.clicked.connect(self._refresh_metrics)
        controls_layout.addWidget(btn_refresh)
        
        # Indicadores de performance
        self.perf_total_label = QLabel("📊 Total Registros: 0")
        self.perf_media_label = QLabel("⏱️ Tempo Médio: 0s")
        self.perf_usuarios_label = QLabel("👥 Usuários Ativos: 0")
        
        for label in [self.perf_total_label, self.perf_media_label, self.perf_usuarios_label]:
            label.setStyleSheet("""
                QLabel {
                    background-color: #ecf0f1;
                    border: 1px solid #bdc3c7;
                    border-radius: 5px;
                    padding: 8px;
                    margin: 2px;
                    font-weight: bold;
                }
            """)
            controls_layout.addWidget(label)
        
        controls_layout.addStretch()
        layout.addWidget(controls_group)

        # Splitter para dividir métricas detalhadas e gráficos
        splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(splitter, stretch=1)

        # Painel esquerdo - Métricas detalhadas
        metrics_widget = QWidget()
        metrics_layout = QVBoxLayout(metrics_widget)
        
        metrics_layout.addWidget(QLabel("📋 Métricas Detalhadas"))
        self.metrics_tree = QTreeWidget()
        self.metrics_tree.setHeaderLabels(["Métrica", "Valor", "Detalhes"])
        self.metrics_tree.header().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.metrics_tree.header().setStretchLastSection(True)
        self.metrics_tree.setStyleSheet("""
            QTreeWidget {
                border: 1px solid #bdc3c7;
                border-radius: 5px;
                background-color: white;
            }
            QTreeWidget::item {
                padding: 5px;
            }
            QTreeWidget::item:selected {
                background-color: #3498db;
                color: white;
            }
        """)
        metrics_layout.addWidget(self.metrics_tree)
        
        splitter.addWidget(metrics_widget)

        # Painel direito - Gráficos
        charts_widget = QWidget()
        charts_layout = QVBoxLayout(charts_widget)

        # Gráfico 1 - Performance por usuário
        charts_layout.addWidget(QLabel("👤 Performance por Usuário"))
        self.fig_user = Figure(figsize=(6, 4))
        self.canvas_user = FigureCanvas(self.fig_user)
        self.canvas_user.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        charts_layout.addWidget(self.canvas_user, stretch=1)

        # Gráfico 2 - Performance por pergunta
        charts_layout.addWidget(QLabel("❓ Performance por Pergunta"))
        self.fig_q = Figure(figsize=(6, 4))
        self.canvas_q = FigureCanvas(self.fig_q)
        self.canvas_q.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        charts_layout.addWidget(self.canvas_q, stretch=1)
        
        splitter.addWidget(charts_widget)
        
        # Define proporções do splitter
        splitter.setSizes([300, 500])

        self.tab_metricas.setLayout(layout)

        # Carrega na inicialização
        if meses:
            self.cmb_mes.setCurrentIndex(len(meses)-1)
        self._refresh_metrics()

        
    @pyqtSlot()
    def _refresh_report(self):
        try:
            # forçar regenerar o relatório usando o mesmo método
            self._on_gerar_parecer_clicked()
        except Exception as e:
            # só loga, não fecha o programa
            log_ui_action('refresh_report_error', {'error': str(e)})
    


    def _refresh_metrics(self):
        """Recarrega dados do Parquet e redesenha JSON + gráficos."""
        mes = self.cmb_mes.currentText()  # e.g. "2025-07"
        if not mes:
            return

        ano, mm = mes.split("-")
        path = rf"\\pfl-cps-file\Divisao_GD\Data\data\performance\stages_{ano}_{mm}.parquet"

        # 1) Leitura do Parquet com tratamento de erro melhorado
        try:
            df = pd.read_parquet(path)
        except FileNotFoundError:
            QMessageBox.warning(self, "Arquivo não encontrado", 
                              f"Arquivo de performance não encontrado para {mes}")
            # Limpa visualizações
            self._clear_metrics_displays()
            return
        except Exception as e:
            QMessageBox.warning(self, "Erro ao ler dados", 
                              f"Erro ao carregar dados de performance:\n{str(e)}")
            self._clear_metrics_displays()
            return

        # 2) Atualiza indicadores rápidos
        total_registros = len(df)
        tempo_medio = df['duration_s'].mean() if 'duration_s' in df.columns else 0
        usuarios_unicos = df['user'].nunique() if 'user' in df.columns else 0
        
        self.perf_total_label.setText(f"📊 Total Registros: {total_registros:,}")
        self.perf_media_label.setText(f"⏱️ Tempo Médio: {tempo_medio:.1f}s")
        self.perf_usuarios_label.setText(f"👥 Usuários Ativos: {usuarios_unicos}")
        
        # Colore indicadores baseado em thresholds
        if tempo_medio > 30:  # Mais de 30 segundos é preocupante
            self.perf_media_label.setStyleSheet("""
                QLabel {
                    background-color: #e74c3c;
                    color: white;
                    border: 1px solid #c0392b;
                    border-radius: 5px;
                    padding: 8px;
                    margin: 2px;
                    font-weight: bold;
                }
            """)
        elif tempo_medio > 15:  # Entre 15-30s é atenção
            self.perf_media_label.setStyleSheet("""
                QLabel {
                    background-color: #f39c12;
                    color: white;
                    border: 1px solid #e67e22;
                    border-radius: 5px;
                    padding: 8px;
                    margin: 2px;
                    font-weight: bold;
                }
            """)
        else:  # Menos de 15s é bom
            self.perf_media_label.setStyleSheet("""
                QLabel {
                    background-color: #27ae60;
                    color: white;
                    border: 1px solid #229954;
                    border-radius: 5px;
                    padding: 8px;
                    margin: 2px;
                    font-weight: bold;
                }
            """)

        # 3) Popula árvore de métricas com estatísticas detalhadas
        self.metrics_tree.clear()
        
        # Métricas por stage
        if 'stage' in df.columns and 'duration_s' in df.columns:
            stage_stats = df.groupby("stage").agg({
                'duration_s': ['count', 'mean', 'std', 'min', 'max']
            }).round(2)
            
            stage_parent = QTreeWidgetItem(self.metrics_tree, ["📊 Por Etapa", "", ""])
            
            for stage in stage_stats.index:
                count = stage_stats.loc[stage, ('duration_s', 'count')]
                mean_time = stage_stats.loc[stage, ('duration_s', 'mean')]
                std_time = stage_stats.loc[stage, ('duration_s', 'std')]
                
                stage_item = QTreeWidgetItem(stage_parent, 
                    [stage, f"{mean_time:.1f}s", f"Count: {count}, Std: {std_time:.1f}s"])
        
        # Métricas por usuário
        if 'user' in df.columns and 'duration_s' in df.columns:
            user_stats = df.groupby("user").agg({
                'duration_s': ['count', 'mean', 'std']
            }).round(2)
            
            user_parent = QTreeWidgetItem(self.metrics_tree, ["👤 Por Usuário", "", ""])
            
            for user in user_stats.index:
                count = user_stats.loc[user, ('duration_s', 'count')]
                mean_time = user_stats.loc[user, ('duration_s', 'mean')]
                std_time = user_stats.loc[user, ('duration_s', 'std')]
                
                user_item = QTreeWidgetItem(user_parent, 
                    [user, f"{mean_time:.1f}s", f"Atividades: {count}, Std: {std_time:.1f}s"])
        
        # Expande os itens principais
        self.metrics_tree.expandAll()

        # 4) Gráfico 1 – média de duração de 'etapa_analise' por usuário
        self.fig_user.clear()
        ax1 = self.fig_user.add_subplot(111)
        
        if 'stage' in df.columns and 'user' in df.columns and 'duration_s' in df.columns:
            df_et = df[df.stage == "etapa_analise"]
            if not df_et.empty:
                media_user = df_et.groupby("user")["duration_s"].mean().sort_values(ascending=True)
                
                if not media_user.empty:
                    bars = ax1.barh(range(len(media_user)), media_user.values)
                    ax1.set_yticks(range(len(media_user)))
                    ax1.set_yticklabels(media_user.index)
                    ax1.set_xlabel("Tempo (segundos)")
                    ax1.set_title("Performance - Etapa Análise por Usuário", fontsize=12, fontweight='bold')
                    
                    # Colore barras baseado na performance
                    for i, bar in enumerate(bars):
                        if media_user.iloc[i] > 30:
                            bar.set_color('#e74c3c')  # Vermelho para lento
                        elif media_user.iloc[i] > 15:
                            bar.set_color('#f39c12')  # Laranja para médio
                        else:
                            bar.set_color('#27ae60')  # Verde para rápido
                    
                    ax1.grid(True, alpha=0.3)
                else:
                    ax1.text(0.5, 0.5, 'Sem dados de etapa_analise', 
                            ha='center', va='center', transform=ax1.transAxes)
            else:
                ax1.text(0.5, 0.5, 'Sem dados de etapa_analise', 
                        ha='center', va='center', transform=ax1.transAxes)
        else:
            ax1.text(0.5, 0.5, 'Dados insuficientes', 
                    ha='center', va='center', transform=ax1.transAxes)
        
        self.fig_user.tight_layout()
        self.canvas_user.draw()

        # 5) Gráfico 2 – média de duração de cada question_* por pergunta
        self.fig_q.clear()
        ax2 = self.fig_q.add_subplot(111)
        
        if 'stage' in df.columns and 'duration_s' in df.columns:
            df_q = df[df.stage.str.startswith("question_")]
            if not df_q.empty:
                media_q = df_q.groupby("stage")["duration_s"].mean().sort_values(ascending=False)
                
                if not media_q.empty:
                    bars = ax2.bar(range(len(media_q)), media_q.values)
                    ax2.set_xticks(range(len(media_q)))
                    ax2.set_xticklabels([stage.replace('question_', 'Q') for stage in media_q.index], 
                                       rotation=45, ha='right')
                    ax2.set_ylabel("Tempo (segundos)")
                    ax2.set_title("Performance por Pergunta", fontsize=12, fontweight='bold')
                    
                    # Colore barras baseado na performance
                    for i, bar in enumerate(bars):
                        if media_q.iloc[i] > 20:
                            bar.set_color('#e74c3c')  # Vermelho para lento
                        elif media_q.iloc[i] > 10:
                            bar.set_color('#f39c12')  # Laranja para médio
                        else:
                            bar.set_color('#27ae60')  # Verde para rápido
                    
                    ax2.grid(True, alpha=0.3)
                else:
                    ax2.text(0.5, 0.5, 'Sem dados de perguntas', 
                            ha='center', va='center', transform=ax2.transAxes)
            else:
                ax2.text(0.5, 0.5, 'Sem dados de perguntas', 
                        ha='center', va='center', transform=ax2.transAxes)
        else:
            ax2.text(0.5, 0.5, 'Dados insuficientes', 
                    ha='center', va='center', transform=ax2.transAxes)
        
        self.fig_q.tight_layout()
        self.canvas_q.draw()
    
    def _clear_metrics_displays(self):
        """Limpa todas as visualizações de métricas."""
        # Limpa indicadores
        self.perf_total_label.setText("📊 Total Registros: 0")
        self.perf_media_label.setText("⏱️ Tempo Médio: 0s")
        self.perf_usuarios_label.setText("👥 Usuários Ativos: 0")
        
        # Limpa árvore
        self.metrics_tree.clear()
        
        # Limpa gráficos
        self.fig_user.clear()
        self.fig_q.clear()
        self.canvas_user.draw()
        self.canvas_q.draw()
    
    # Handlers de eventos
    
    def _on_tab_changed(self, index):
        """Handler para mudança de tab."""
        tab_name = self.tabs.tabText(index)
        log_ui_action('tab_changed', {'tab': tab_name})
        self.status_bar.showMessage(f"Tab atual: {tab_name}")
    
    def _on_consultar_clicked(self):
        """Handler para botão Consultar Notas."""
        with PerformanceTracker("consultar_notas_ui") as tracker:
            log_ui_action('consultar_clicked')
            self.status_bar.showMessage("Consultando notas...")

            # 1) Consulta Oracle com tratamento de erros
            try:
                from app.database.oracle_connector import consulta_notas_oracle
                notas = consulta_notas_oracle()
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Erro ao consultar Oracle",
                    f"Falha ao buscar notas no Oracle:\n{e}"
                )
                self.status_bar.showMessage("Erro na consulta de notas")
                return

            # 2) Enriquecer cada nota com tipo de projeto
            for nota in notas:
                nota["TIPO_PROJETO"] = calcular_tipo_projeto(
                    nota.get("DT_PARECER"),
                    nota.get("DT_CADASTRO"),
                    nota.get("CD_STATUS")
                )

            # 3) Armazena e aplica filtros normalmente
            self.all_notes = notas
            self._apply_filters()
            if hasattr(self, 'tab_gestao'):
                self.tab_gestao.set_notes_data(self.filtered_notes)

            tracker.add_detail("items_count", len(notas))
            self.status_bar.showMessage("Consulta concluída")
    
            
    def _on_atualizar_clicked(self):
        """Handler para botão Atualizar."""
        log_ui_action('atualizar_clicked')
        self.status_bar.showMessage("Atualizando...")
        # Implementação real chamaria novamente a consulta
        self._on_consultar_clicked()
    
    def _on_nota_selected(self, note):
        """
        Handler para seleção de nota na árvore.

        Args:
            note (dict): Nota selecionada.
        """
        atividade = note.get('NR_ATIVIDADE', '')
        uc = note.get('CD_UC', '')
        log_ui_action('nota_selected', {'atividade': atividade, 'uc': uc})
        self.status_bar.showMessage(f"Nota selecionada: Atividade {atividade}, UC {uc}")

        # # 1) Consulta dados da UC no HANA, com tratamento de erros
        # try:
        #     from app.database.hana_connector import consultar_uc_hana
        #     uc_data = consultar_uc_hana(uc)
        # except Exception as e:
        #     QMessageBox.critical(
        #         self,
        #         "Erro ao consultar SAP HANA",
        #         f"Falha ao se conectar ou consultar o SAP HANA:\n{e}"
        #     )
        #     return

        # # 2) Se não retornou nada (consulta ok, mas sem contrato)
        # if not uc_data:
        #     QMessageBox.warning(
        #         self,
        #         "Contrato Não Encontrado",
        #         "Não foi encontrado contrato ativo no sistema.\n"
        #         "A análise será automaticamente INDEFERIDA."
        #     )
            # self.analysis_form.decision_tree.flags[29] = 1

        # 3) Atualiza o formulário de análise (mesmo que uc_data esteja vazio)
        # self.analysis_form.set_note_data(note, uc_data)
        self.analysis_form.set_note_data(note, {})
    @pyqtSlot()
    def _on_avancar_clicked(self):
        log_ui_action('avancar_clicked')
        
        # 1) Obtém a nota e tenta bloquear
        note = self.tree_notas.get_selected_note()
        if not note:
            QMessageBox.warning(self, "Aviso", "Selecione uma nota para análise.")
            return

        nr_atividade = str(note.get("NR_ATIVIDADE", ""))
        metrics_manager.start_stage(nr_atividade, "etapa_analise")
        
        if not self.lock_manager.is_note_locked_by_me(nr_atividade):
            success = self.lock_manager.lock_note(nr_atividade)
            if not success:
                QMessageBox.warning(
                    self, "Erro de Bloqueio",
                    "Não foi possível bloquear a nota para análise.\n"
                    "Verifique se ela não está sendo analisada por outro usuário."
                )
                return
            # atualiza árvore e garante o item selecionado
            self.tree_notas._update_tree()
            for i in range(self.tree_notas.topLevelItemCount()):
                item = self.tree_notas.topLevelItem(i)
                atividade = item.data(0, Qt.UserRole)
                if atividade and str(atividade).strip() == nr_atividade.strip():
                    self.tree_notas.setCurrentItem(item)
                    break
        
        # 2) Garante o download (cache na rede ou refresh local)
        #    skip_move=True se quiser manter no Downloads local quando recarregar
        folder, valores_site = self._ensure_downloaded(
            nr_atividade,
            str(note.get('CD_PROJETO', '')),
            skip_move=True
        )
        
        # 3) Carrega dados da UC no HANA
        uc_data = {}
        if note.get('CD_UC'):
            try:
                from app.database.hana_connector import consultar_uc_hana
                uc_data = consultar_uc_hana(note['CD_UC'])
            except Exception as e:
                print(f"Erro ao consultar UC: {e}")
        
        # 4) Atualiza o AnalysisForm com tudo
        self.analysis_form.set_note_data(note, uc_data)
        self.analysis_form.valores_site = valores_site
        self.analysis_form.set_downloads_folder(folder)
        self.analysis_form.populate_attachments(folder)
        
        # 5) Muda para a tab de análise e prepara para iniciar
        self.tabs.setCurrentIndex(1)
        self.status_bar.showMessage("Pronto para análise")
        # Se quiser disparar a análise automaticamente:
        # self.analysis_form.start_analysis()
            
    
        
    
    @pyqtSlot(dict, dict)
    def _on_download_complete(self, result: dict, valores_site: dict):
        """
        Recebe o resultado do download e os valores extraídos do site,
        injeta no AnalysisForm e só então dispara a análise.
        """
        # 1) Reabilita o botão
        self.btn_baixar_anexos.setEnabled(True)

        if not result.get("success"):
            self.status_bar.showMessage("Erro no download")
            QMessageBox.warning(
                self, "Erro no Download",
                f"Ocorreu um erro ao baixar os anexos:\n{result['message']}"
            )
            return

        # 2) Feedback visual
        self.status_bar.showMessage(result["message"])
        QMessageBox.information(
            self, "Download Concluído",
            f"{result['message']}\n\nArquivos em:\n{result['downloads_folder']}"
        )
        os.startfile(result["downloads_folder"])

        # 3) Injeta no AnalysisForm
        self.analysis_form.valores_site = valores_site
        self.analysis_form.set_downloads_folder(result["downloads_folder"])
        self.analysis_form.populate_attachments(result["downloads_folder"])

        # 4) Finalmente, inicia a análise
        self.analysis_form.start_analysis()

        
    def _on_limpar_flags_clicked(self):
        """Handler para botão Limpar Flags."""
        log_ui_action('limpar_flags_clicked')
        
        # Confirma a ação
        reply = QMessageBox.question(
            self, 'Confirmar Ação',
            "Tem certeza que deseja limpar todas as flags?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Limpa as flags
            if self.flags_manager:
                self.flags_manager.clear_all_flags()
            
            self.flags_view.clear_flags()
            self.status_bar.showMessage("Flags limpas")
    
    def _on_question_answered(self, question_id, answer):
        """
        Handler para resposta de pergunta.
        
        Args:
            question_id (str): Identificador da pergunta.
            answer (str): Resposta selecionada.
        """
        log_ui_action('question_answered_main', {
            'question_id': question_id,
            'answer': answer
        })
        
        # Atualiza as flags na visualização
        if self.flags_manager:
            flags = self.flags_manager.get_active_flags()
            self.flags_view.set_flags(flags)
        note = self.tree_notas.get_selected_note()
        if note:
            nr_atividade = str(note.get("NR_ATIVIDADE", ""))
            metrics_manager.record_analysis_step(nr_atividade, step_name=question_id)
    
    def _on_analysis_completed(self):
        """Handler para conclusão da análise."""
        log_ui_action('analysis_completed_main')
        self.status_bar.showMessage("Análise concluída")
        metrics_manager.export_now()
        
        # Habilita o botão de gerar parecer
        self.btn_gerar_parecer.setEnabled(True)
    
    def _on_gerar_parecer_clicked(self):
        """Handler para botão Gerar Parecer."""
        log_ui_action('gerar_parecer_clicked')
        self.status_bar.showMessage("Gerando parecer...")

        # 1) Obtém a nota selecionada
        note = self.tree_notas.get_selected_note()
        if not note:
            QMessageBox.warning(self, "Aviso", "Selecione uma nota para gerar o parecer.")
            return

        # 2) Extrai a escolha de Fast Track da árvore
        dt = self.analysis_form.decision_tree
        fast_opt = dt.history.get("fast_track", "não").strip().lower()
        log_ui_action('debug_fast_opt_before_report', {'fast_opt': fast_opt})

        # 3) Grava no mesmo campo que o ReportGenerator vai ler
        note["fast_track"] = fast_opt

        # 2) Consulta dados da UC no HANA
        uc = note.get('CD_UC', '')
        from app.database.hana_connector import consultar_uc_hana
        # uc_data = consultar_uc_hana(uc)
        uc_data = getattr(self.analysis_form, 'uc_data', {})

        # 3) Detecta se há indeferimento pela árvore de decisão
        has_indeferimento = False
        dt_flags = {}
        if hasattr(self, 'analysis_form') and hasattr(self.analysis_form, 'decision_tree'):
            dt = self.analysis_form.decision_tree
            dt_flags = getattr(dt, 'flags', {})
            for flag_id, value in dt_flags.items():
                if flag_id not in ['flag_91_sim', 'flag_91_nao'] and value:
                    has_indeferimento = True
                    break

        # 4) Pega opções de prazo da UI
        opts = self.results_view.get_deadline_options()
        with_deadline = opts['with_deadline']
        deadline_days = opts['deadline_days']

        # 5) Monta o corpo do parecer
        if has_indeferimento:
            corpo = []
            corpo.append("Prezado(a) Cliente,")
            corpo.append("")

            intro = (
                f"Analisamos seu projeto de geração distribuída para a instalação {uc}, "
                f"atividade {note.get('NR_ATIVIDADE', '')}"
            )
            if uc_data.get('NOME_RAZAO'):
                intro += f", {uc_data['NOME_RAZAO']}"
            intro += ", e informamos que seu projeto foi INDEFERIDO."
            corpo.append(intro)
            corpo.append("")

            # Flags agrupadas por cabeçalho
            from app.config import constants
            grouped = {}
            for flag_id, value in dt_flags.items():
                if flag_id not in ['flag_91_sim', 'flag_91_nao'] and value:
                    info = constants.FLAG_INFO.get(flag_id, {})
                    hdr = info.get('cabecalho', 'OUTROS')
                    txt = info.get('texto', f'Flag {flag_id}')
                    grouped.setdefault(hdr, []).append(txt)

            for hdr, textos in grouped.items():
                corpo.append(f"{hdr}:")
                for t in textos:
                    corpo.append(f"- {t}")
                corpo.append("")

            # ─── Novo bloco: Informações Importantes ───────────────────────────────────────────
            corpo.append("Informações Importantes:")
            corpo.append("(A) Esta atividade não tem mais validade, desta forma, pedimos a gentileza de movê-la no box de projetos encerrados.")
            corpo.append("(B) Ao apresentar uma nova atividade, atentar-se à uniformidade das informações que constam entre os documentos e os campos preenchíveis no site, além dos documentos a serem anexados nessa nova atividade.")
            corpo.append("Lembre-se: por se tratar de uma nova atividade, toda documentação solicitada nas normas da CPFL deve ser apresentada, e utilizar sempre as normas atualizadas no site da CPFL.")
            corpo.append("Colocamo-nos à disposição para outros esclarecimentos necessários.")
            corpo.append("")  # linha em branco antes do prazo
            # ──────────────────────────────────────────────────────────────────────────────────

            # Insere prazo e instruções de reenvio SE marcado
            if with_deadline:
                limite = (datetime.now() + timedelta(days=deadline_days)).strftime("%d/%m/%Y")
                corpo.append(f"Solicitamos que os ajustes sejam realizados até {limite}.")
                corpo.append("")
                corpo.append(
                    "Após realizar os ajustes solicitados, favor anexar os documentos "
                    "no site Projetos Particulares."
                )
                corpo.append("")

            corpo.append("Atenciosamente,")
            corpo.append("Comunicação CPFL - Projetos Particulares")
            parecer = "\n".join(corpo)

        else:
            # DEFERIMENTO
            try:
                parecer = self.report_generator.generate_report(
                    nota_info=note,
                    uc_info=uc_data,
                    prazo=deadline_days
                )
            except Exception:
                # Fallback manual
                corpo = []
                corpo.append("Prezado(a) Cliente,")
                corpo.append("")
                intro = (
                    f"Analisamos seu projeto de geração distribuída para a instalação {uc}, "
                    f"atividade {note.get('NR_ATIVIDADE', '')}"
                )
                if uc_data.get('NOME_RAZAO'):
                    intro += f", {uc_data['NOME_RAZAO']}"
                intro += ", e informamos que seu projeto foi DEFERIDO."
                corpo.append(intro)
                corpo.append("")
                corpo.append("Seu projeto atende a todos os requisitos técnicos e comerciais necessários.")
                corpo.append("")

                if with_deadline:
                    limite = (datetime.now() + timedelta(days=deadline_days)).strftime("%d/%m/%Y")
                    corpo.append(f"Solicitamos que os ajustes sejam realizados até {limite}.")
                    corpo.append("")
                    corpo.append(
                        "Após realizar os ajustes solicitados, favor anexar os documentos "
                        "no site Projetos Particulares."
                    )
                    corpo.append("")

                corpo.append("Atenciosamente,")
                corpo.append("Equipe de Análise de Projetos - CPFL")
                parecer = "\n".join(corpo)

            # Se não quiser prazo, remova as linhas de prazo
            if not with_deadline:
                linhas = [
                    l for l in parecer.splitlines()
                    if not l.startswith("Solicitamos que os ajustes") 
                    and "favor anexar os documentos" not in l
                ]
                parecer = "\n".join(linhas)

        # 6) Log da geração
        status = "indeferido" if has_indeferimento else "deferido"
        log_ui_action('report_generated', {
            'nr_atividade': note.get('NR_ATIVIDADE', ''),
            'status': status,
            'has_indeferimento': has_indeferimento
        })

        # 7) Atualiza a view e muda para a aba Resultados
        self.results_view.set_report_text(parecer)
        self.tabs.setCurrentIndex(2)
        self.status_bar.showMessage(f"Parecer gerado com sucesso - Status: {status.upper()}")
        nr_atividade = str(note.get("NR_ATIVIDADE", ""))
        metrics_manager.end_stage(nr_atividade, "etapa_analise")
        # metrics_manager.end_stage(nr_atividade, "etapa_parecer")
        metrics_manager.export_now()



            
    def _on_copiar_clicked(self):
        """Handler para botão Copiar Parecer."""
        log_ui_action('copiar_clicked')
        
        # Copia o texto para a área de transferência
        self.results_view.copy_to_clipboard()
        self.status_bar.showMessage("Parecer copiado para a área de transferência")
    
    def _on_salvar_clicked(self):
        """Handler para botão Salvar Parecer."""
        log_ui_action('salvar_clicked')
        
        # Obtém o texto do parecer
        parecer = self.results_view.get_report_text()
        if not parecer:
            QMessageBox.warning(self, "Aviso", "Não há parecer para salvar.")
            return
        
        # Obtém a nota selecionada
        note = self.tree_notas.get_selected_note()
        if not note:
            QMessageBox.warning(self, "Aviso", "Selecione uma nota para salvar o parecer.")
            return
        
        # Obtém o caminho para salvar
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Salvar Parecer",
            f"Parecer_Atividade_{note.get('NR_ATIVIDADE', 'desconhecida')}.txt",
            "Arquivos de Texto (*.txt);;Todos os Arquivos (*)"
        )
        
        if not file_path:
            return
        
        # Salva o parecer
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(parecer)
            
            self.status_bar.showMessage(f"Parecer salvo em {file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao salvar o parecer: {str(e)}")
    
    def _on_enviar_email_clicked(self):
        """Handler para botão Enviar por E-mail."""
        log_ui_action('enviar_email_clicked')

        # 1) Confirma a ação
        reply = QMessageBox.question(
            self, 'Confirmar Envio',
            "Tem certeza que deseja enviar o parecer por e-mail?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return

        # 2) Reúne dados do parecer e das flags
        note = self.tree_notas.get_selected_note()
        nr = note.get('NR_ATIVIDADE', '')
        uc = note.get('CD_UC', '')
        cliente = self.analysis_form.uc_data.get('NOME_RAZAO', '')
        dt = self.analysis_form.decision_tree
        flags = {fid: val for fid, val in getattr(dt, 'flags', {}).items() if val}

        # 3) Agrupa as flags por cabeçalho (usa seus constantes)
        from app.config.constants import FLAG_INFO
        grouped = {}
        for fid in flags:
            info = FLAG_INFO.get(fid, {})
            hdr = info.get('cabecalho', 'OUTROS').upper()
            txt = info.get('texto', f'Flag {fid}')
            grouped.setdefault(hdr, []).append(txt)

        # 4) Monta o HTML
        html = []
        html.append("<p>Prezado(a) Cliente,</p>")
        html.append(f"<p>Analisamos seu projeto de geração distribuída para a instalação "
                    f"<strong>{uc}</strong>, atividade <strong>{nr}</strong>"
                    f"{', ' + cliente if cliente else ''}, e informamos que seu projeto foi "
                    f"<strong>INDEFERIDO</strong>.</p>")

        # Para cada seção de flags
        for hdr, items in grouped.items():
            html.append(f"<h4>-----(x) {hdr}:</h4>")
            html.append("<ul>")
            for t in items:
                html.append(f"  <li>{t}</li>")
            html.append("</ul>")

        # Informações Importantes
        html.append("<h4>Informações Importantes:</h4>")
        html.append("<ol>")
        html.append("<li>(A) Esta atividade não tem mais validade, desta forma, pedimos a gentileza de movê-la no box de projetos encerrados.</li>")
        html.append("<li>(B) Ao apresentar uma nova atividade, atentar-se à uniformidade das informações que constam entre os documentos "
                    "e os campos preenchíveis no site, além dos documentos a serem anexados nessa nova atividade.</li>")
        html.append("<li>Por se tratar de uma nova atividade, toda documentação solicitada nas normas da CPFL deve ser apresentada, "
                    "utilizando sempre as normas atualizadas no site da CPFL.</li>")
        html.append("</ol>")

        html.append("<p>Atenciosamente,<br/>Equipe de Análise de Projetos - CPFL</p>")
        html.append("<hr/>")
        html.append("<small>Esta mensagem (incluindo anexos, se houver) pode conter dados e informações confidenciais... "
                    "Caso tenha recebido esta mensagem erroneamente, por favor notifique o remetente e providencie imediata exclusão.</small>")

        full_html = "\n".join(html)
        
        # pega o login do Windows/Linux
        login = getpass.getuser()

        # monta o e-mail
        if login == "2006428":
            destinatario = "bgobbi@cpfl.com.br"
        else:
            destinatario = "tecnicogdpaulista@cpfl.com.br"

        # 5) Envia pelo Power Automate
        sucesso = enviar_email_power_automate_html(
            destinatario,
            f"Parecer Atividade {nr}",
            full_html
        )

        # 6) Feedback ao usuário
        if sucesso:
            self.status_bar.showMessage("E-mail enviado com sucesso")
        else:
            QMessageBox.critical(self, "Erro", "Falha ao enviar o e-mail")

        
    def _on_atualizar_metricas_clicked(self):
        """Handler para botão Atualizar Métricas."""
        log_ui_action('atualizar_metricas_clicked')
        self.status_bar.showMessage("Atualizando métricas...")
        
        # Aqui seria implementada a lógica de atualização de métricas
        QTimer.singleShot(500, lambda: self.status_bar.showMessage("Métricas atualizadas"))
    
    def _on_exportar_metricas_clicked(self):
        """Handler para botão Exportar Métricas."""
        log_ui_action('exportar_metricas_clicked')
        
        # Aqui seria implementada a lógica de exportação de métricas
        self.status_bar.showMessage("Métricas exportadas com sucesso")

    @pyqtSlot()
    def _on_filtro_changed(self):
        """
        Slot exposto para o filtro de notas.
        Apenas delega para o helper em filters_integration.py.
        """
        # from app.ui.filters_integration import _on_filtro_changed as _fi_slot
        # _fi_slot(self)
    
    def closeEvent(self, event):
        """
        Handler para evento de fechamento da janela.
        
        Args:
            event: Evento de fechamento.
        """
        # Desbloqueia todas as notas do usuário atual
        if self.lock_manager:
            count = self.lock_manager.unlock_all_my_notes()
            log_ui_action('notes_unlocked_on_exit', {'count': count})
     
        from app.utils.logger import close_metrics       
        close_metrics()
        
        # Aceita o evento de fechamento
        event.accept()
    
    # Função para calcular o status com base na data de prazo
    def calcular_status(data_prazo_str):
        """
        Calcula o status com base na data de prazo.
        Args:
            data_prazo_str (str): Data de prazo no formato 'YYYY-MM-DD'.
        Returns:
            str: Status calculado (D0, D1, D2, etc.).
        """
        if not data_prazo_str:
            return ""
        try:
            data_prazo = datetime.strptime(data_prazo_str, "%Y-%m-%d")
            hoje = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            diferenca = (hoje - data_prazo).days
            if diferenca < 0:
                return ""  # Data futura
            elif diferenca > 7:
                return "D7+"
            else:
                return f"D{diferenca}"
        except Exception as e:
            print(f"Erro ao calcular status: {e}")
            return ""
        
    def _on_exportar_notas_clicked(self):
        """Exporta todo o conteúdo da tree_notas para um arquivo CSV."""
        # 1) Recupera cabeçalhos
        headers = [self.tree_notas.headerItem().text(col)
                   for col in range(self.tree_notas.columnCount())]

        # 2) Percorre cada linha da tree
        data_rows = []
        for row in range(self.tree_notas.topLevelItemCount()):
            item = self.tree_notas.topLevelItem(row)
            row_data = [item.text(col) for col in range(self.tree_notas.columnCount())]
            data_rows.append(row_data)

        # 3) Pergunta onde salvar
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Salvar Notas como CSV",
            "notas.csv",
            "CSV (*.csv);;Todos os Arquivos (*)"
        )
        if not path:
            return  # usuário cancelou

        # 4) Gravação
        try:
            with open(path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(headers)
                writer.writerows(data_rows)
            self.status_bar.showMessage(f"Notas exportadas em {path}")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Falha ao exportar notas:\n{e}")

    # Código a ser integrado à classe MainWindow

    class _DownloadThread(QThread):
        # sinal que manda dois dicts: o resultado e os valores_site
        download_complete = pyqtSignal(dict, dict)

        def __init__(self, atividade: str, cd_projeto: str):
            super().__init__()
            self.atividade  = atividade
            self.cd_projeto = cd_projeto

        def run(self):
            try:
                log_ui_action('download_thread_start', {
                    'atividade': self.atividade, 'projeto': self.cd_projeto
                })
                # chamar seu método que retorna (pasta, valores_site)
                downloads_folder, valores_site = abrir_atividade(self.atividade, self.cd_projeto)
                log_ui_action('download_thread_success', {
                    'downloads_folder': downloads_folder, 'valores_site': valores_site
                })
                self.download_complete.emit(
                    {"success": True, "message": f"Download concluído.", "downloads_folder": downloads_folder},
                    valores_site
                )
            except Exception as e:
                log_ui_action('download_thread_error', {'error': str(e)})
                self.download_complete.emit(
                    {"success": False, "message": str(e), "downloads_folder": None},
                    {}
                )

    def _on_baixar_anexos_clicked(self):
        """Handler para botão Baixar Anexos."""
        log_ui_action('baixar_anexos_clicked')

        note = self.tree_notas.get_selected_note()
        if not note:
            QMessageBox.warning(self, "Aviso", "Selecione uma nota para baixar anexos.")
            return

        atividade  = str(note.get('NR_ATIVIDADE', ''))
        cd_projeto = str(note.get('CD_PROJETO', ''))
        if not cd_projeto:
            QMessageBox.warning(self, "Aviso", "Código do projeto não disponível.")
            return

        self.status_bar.showMessage("Iniciando download de anexos...")
        self.btn_baixar_anexos.setEnabled(False)

        # dispara thread de download
        self._download_thread = MainWindow._DownloadThread(atividade, cd_projeto)
        self._download_thread.download_complete.connect(self._on_download_complete)
        self._download_thread.start()
