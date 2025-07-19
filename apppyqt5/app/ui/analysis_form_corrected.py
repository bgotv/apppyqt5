"""
Formulário de análise de notas técnicas.AnalysisForm
"""
import os
import re
import time
import threading
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTextEdit, QMessageBox, QProgressBar, QGroupBox, QFormLayout,
    QScrollArea, QFrame, QSplitter, QCheckBox, QListWidget, QListWidgetItem, QTreeWidget, QTreeWidgetItem
)
from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtGui import QFont, QIcon

from app.core.decision_tree import DecisionTree
from app.core.flags_manager import FlagsManager
from app.core.report_generator import ReportGenerator
from app.ui.web_automation_manager import WebAutomationManager
from app.utils.logger import log_action, metrics_manager
from PyQt5.QtWidgets import QTreeView, QHeaderView
from app.core.decision_tree import OptionDialog, CheckboxDialog
from PyQt5.QtCore import QEventLoop, Qt
from PyQt5.QtWidgets import QSplitter

class AnalysisForm(QWidget):
    """
    Formulário para análise de notas técnicas.
    """
    question_answered  = pyqtSignal(str, str)   # question_id, answer
    analysis_completed = pyqtSignal()
    # Sinais
    analysis_completed = pyqtSignal()
    
    def __init__(self, parent=None, lock_manager=None):
        """
        Inicializa o formulário de análise.
        
        Args:
            parent (QWidget, optional): Widget pai.
            lock_manager (NotesLockManager, optional): Gerenciador de bloqueio de notas.
        """
        super().__init__(parent)
        self.parent = parent
        self.lock_manager = lock_manager
        self.note_data = {}
        self.uc_data = {}
        self.downloads_folder = None
        self.analysis_in_progress = False
        
        # Inicializa componentes
        self.flags_manager = FlagsManager()
        self.report_generator = ReportGenerator(self.flags_manager)
        self.decision_tree = DecisionTree(self.flags_manager, self)
        
        # Conecta sinais
        if hasattr(self.decision_tree, 'analysis_completed') and self.decision_tree.analysis_completed is not None:
            self.decision_tree.analysis_completed.connect(self._on_analysis_completed)
        else:
            # Se o sinal não existir, usamos uma abordagem alternativa
            # Podemos verificar periodicamente o status da análise ou
            # implementar um callback na árvore de decisão
            pass
        
        # Inicializa a interface
        self._init_ui()
        
        def inline_exec_option(dlg, *args, **kwargs):
            # `dlg` aqui é a instância de OptionDialog
            dlg.setParent(self.inline_area)
            dlg.setWindowFlags(Qt.Widget)
            self.inline_area.layout().addWidget(dlg)
            dlg.show()
            loop = QEventLoop()
            dlg.accepted.connect(loop.quit)
            loop.exec_()
            dlg.hide()
            return 1  # sinal de Accepted

        def inline_exec_checkbox(dlg, *args, **kwargs):
            # `dlg` é a instância de CheckboxDialog
            dlg.setParent(self.inline_area)
            dlg.setWindowFlags(Qt.Widget)
            self.inline_area.layout().addWidget(dlg)
            dlg.show()
            loop = QEventLoop()
            dlg.ok_button.clicked.connect(loop.quit)
            loop.exec_()
            dlg.hide()
            return 1

        # Aplique o patch **apenas** uma vez:
        OptionDialog.exec_   = inline_exec_option
        CheckboxDialog.exec_ = inline_exec_checkbox
        
        self.perguntas = [
            {'key': 'qnt_mod_site',           'texto': 'Quantidade de Módulos'},
            {'key': 'qnt_inv_site',           'texto': 'Quantidade de Inversores'},
            {'key': 'potencia_total_mod_site','texto': 'Potência Total dos Módulos'},
            {'key': 'modelo_mod_site',        'texto': 'Modelo dos Módulos'},
            {'key': 'modelo_inv_site',        'texto': 'Modelo dos Inversores'},
            {'key': 'potencia_total_inv_site',     'texto': 'Potência Total dos Inversores'},
        ]
    
    def _init_ui(self):
        """Inicializa a interface do usuário."""
        # Layout principal
        main_layout = QVBoxLayout(self)
        
        # Área de informações da nota
        info_group = QGroupBox("Informações da Nota")
        info_layout = QFormLayout()
        
        self.lbl_nr_atividade = QLabel()
        self.lbl_nr_atividade.setTextInteractionFlags(Qt.TextSelectableByMouse)
        info_layout.addRow("Número da Atividade:", self.lbl_nr_atividade)
        
        self.lbl_cliente = QLabel()
        self.lbl_cliente.setTextInteractionFlags(Qt.TextSelectableByMouse)
        info_layout.addRow("Cliente:", self.lbl_cliente)
        
        self.lbl_uc = QLabel()
        self.lbl_uc.setTextInteractionFlags(Qt.TextSelectableByMouse)
        info_layout.addRow("UC:", self.lbl_uc)
        
        self.lbl_tipo = QLabel()
        self.lbl_tipo.setTextInteractionFlags(Qt.TextSelectableByMouse)
        info_layout.addRow("Tipo:", self.lbl_tipo)
        
        info_group.setLayout(info_layout)
        main_layout.addWidget(info_group)
        
        # Área de ações
        actions_layout = QHBoxLayout()
        
        self.btn_iniciar_analise = QPushButton("Iniciar Análise")
        self.btn_iniciar_analise.clicked.connect(self._on_iniciar_analise_clicked)
        actions_layout.addWidget(self.btn_iniciar_analise)
        
        self.btn_abrir_anexos = QPushButton("Abrir Pasta de Anexos")
        self.btn_abrir_anexos.clicked.connect(self._on_abrir_anexos_clicked)
        self.btn_abrir_anexos.setEnabled(False)
        actions_layout.addWidget(self.btn_abrir_anexos)
        
        # self.btn_gerar_parecer = QPushButton("Gerar Parecer")
        # self.btn_gerar_parecer.clicked.connect(self._on_gerar_parecer_clicked)
        # self.btn_gerar_parecer.setEnabled(False)
        # actions_layout.addWidget(self.btn_gerar_parecer)
        
        main_layout.addLayout(actions_layout)
        
        # Área de progresso
        progress_layout = QHBoxLayout()
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("%p% - %v de %m")
        progress_layout.addWidget(self.progress_bar)
        
        self.lbl_status = QLabel("Pronto para análise")
        progress_layout.addWidget(self.lbl_status)
        
        main_layout.addLayout(progress_layout)
        
        self.inline_area = QWidget()
        self.inline_area.setLayout(QVBoxLayout())
        main_layout.addWidget(self.inline_area)
        
        # 1) Cria os dois grupos, mas NÃO adiciona attachments_group diretamente:
        attachments_group = QGroupBox("Anexos")
        attachments_layout = QVBoxLayout(attachments_group)
        self.tree_attachments = QTreeWidget()
        self.tree_attachments.setHeaderLabels(["Categoria / Arquivo"])
        self.tree_attachments.itemDoubleClicked.connect(self._on_open_attachment)
        attachments_layout.addWidget(self.tree_attachments)

        results_group = QGroupBox("Resultados da Análise")
        results_layout = QVBoxLayout(results_group)
        self.txt_results = QTextEdit()
        self.txt_results.setReadOnly(True)
        results_layout.addWidget(self.txt_results)

        # 2) Coloca ambos num splitter horizontal
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(results_group)
        splitter.addWidget(attachments_group)
        splitter.setStretchFactor(0, 7)
        splitter.setStretchFactor(1, 3)

        # 3) Adiciona ao layout principal
        main_layout.addWidget(splitter, 1)
        

        try:# Cria o widget QTreeView
# ─── Nova área: Dados Extraídos do Site ─────────────────────────────────
            site_group  = QGroupBox("Dados Extraídos do Site")
            site_layout = QVBoxLayout()

            self.treeView = QTreeView()
            # 1) Cria e já associa um modelo vazio
            model = QStandardItemModel()
            model.setHorizontalHeaderLabels(['Variável', 'Valor'])
            self.treeView.setModel(model)

            # 2) Só aí mexe no header, com fallback para versões antigas do Qt
            header = self.treeView.header()
            if hasattr(header, 'setSectionResizeMode'):
                header.setSectionResizeMode(0, QHeaderView.Stretch)
            else:
                header.setResizeMode(0, QHeaderView.Stretch)
            header.setStretchLastSection(False)

            site_layout.addWidget(self.treeView)
            site_group.setLayout(site_layout)
            main_layout.addWidget(site_group)
            site_group.hide()
        except Exception as e:
            print("Erro ao criar árvore:", e)
            raise
        


        
    def populate_attachments(self, folder: str):
        """
        Preenche self.tree_attachments agrupando por categoria,
        casando tolerante a múltiplos espaços, filtra categorias
        indesejadas e omite as que ficarem vazias.
        """
        self.tree_attachments.clear()
        categorias = getattr(self, 'valores_site', {}) \
                        .get('anexos_por_categoria', {})

        IGNORE_CATS = {
            "ANEXOS",
            "DOCUMENTOS PARA ANÁLISE DA PROTEÇÃO"
        }

        # 1) Lista física de arquivos e seu mapeamento normalizado → real
        arquivos_fisicos = os.listdir(folder)
        norm_map = {}
        for fn in arquivos_fisicos:
            key = re.sub(r'\s+', ' ', fn).strip().lower()
            norm_map[key] = fn

        # 2) Para cada categoria do site
        for categoria, lista_display in categorias.items():
            cat_key = categoria.strip().upper()

            # 2.1) pula categorias indesejadas ou vazias
            if cat_key in IGNORE_CATS or not lista_display:
                continue

            # 2.2) cria nó de categoria
            cat_item = QTreeWidgetItem(self.tree_attachments, [categoria])
            cat_item.setFirstColumnSpanned(True)

            # 2.3) tenta casar cada texto com um arquivo real
            for display_txt in lista_display:
                # remove prefixo de data “dd/mm/yyyy - ”
                nome_limpo = re.sub(r'^\d{2}/\d{2}/\d{4}\s*-\s*', '', display_txt)
                # normaliza espaços e case
                lookup = re.sub(r'\s+', ' ', nome_limpo).strip().lower()

                # 1º: busca exato
                real_fn = norm_map.get(lookup)
                # 2º: fallback por substring
                if not real_fn:
                    for key, fn in norm_map.items():
                        if lookup in key:
                            real_fn = fn
                            break

                path = os.path.join(folder, real_fn) if real_fn else None

                filho = QTreeWidgetItem(cat_item, [display_txt])
                filho.setData(0, Qt.UserRole, path)

            # 2.4) se não houve nenhum filho com path válido, remove a categoria
            if cat_item.childCount() == 0:
                idx = self.tree_attachments.indexOfTopLevelItem(cat_item)
                self.tree_attachments.takeTopLevelItem(idx)
            else:
                cat_item.setExpanded(True)

        self.tree_attachments.expandAll()


    def _on_open_attachment(self, item: QTreeWidgetItem, column: int):
        # só abre se for folha (tem parent)
        if item.parent() is None:
            return
        path = item.data(0, Qt.UserRole)
        if path and os.path.exists(path):
            os.startfile(path)
        else:
            QMessageBox.warning(self, "Arquivo não encontrado", f"{path} não existe.")
    
    def set_note_data(self, note_data, uc_data=None):
        """
        Define os dados da nota para análise.
        
        Args:
            note_data (dict): Dados da nota técnica.
            uc_data (dict, optional): Dados da unidade consumidora.
        """
        self.note_data = note_data or {}
        self.uc_data = uc_data or {}
        
        # Reseta completamente o estado da análise anterior
        self._reset_analysis_state()
        
        # Atualiza a interface com os dados da nota
        self.lbl_nr_atividade.setText(str(self.note_data.get("NR_ATIVIDADE", "")))
        self.lbl_cliente.setText(str(self.note_data.get("NM_CLIENTE", "")))
        self.lbl_uc.setText(str(self.note_data.get("CD_UC", "")))
        self.lbl_tipo.setText(str(self.note_data.get("TIPO_DOCUMENTO", "")))
        
        # Limpa resultados anteriores
        self.txt_results.clear()
        self.progress_bar.setValue(0)
        self.lbl_status.setText("Pronto para análise")
        
        # Reseta flags e histórico
        self.flags_manager.clear_all_flags()
        self.decision_tree.clear_history()
        
        # Habilita/desabilita botões
        self.btn_iniciar_analise.setEnabled(True)
        self.btn_abrir_anexos.setEnabled(False)
        # self.btn_gerar_parecer.setEnabled(False)
        
        log_action('note_data_set', {
            'nr_atividade': self.note_data.get("NR_ATIVIDADE", ""),
            'cd_uc': self.note_data.get("CD_UC", "")
        })
    
    def _reset_analysis_state(self):
        """
        Reseta completamente o estado da análise anterior para evitar 
        confusão entre diferentes atividades.
        """
        # Reseta variáveis de dados do site
        if hasattr(self, 'valores_site'):
            delattr(self, 'valores_site')
        
        # Reseta pasta de downloads
        self.downloads_folder = None
        
        # Reseta estado de análise
        self.analysis_in_progress = False
        
        # Limpa lista de anexos
        if hasattr(self, 'tree_attachments'):
            self.tree_attachments.clear()
        
        # Limpa área inline de perguntas
        if hasattr(self, 'inline_area') and self.inline_area.layout():
            # Remove todos os widgets da área inline
            layout = self.inline_area.layout()
            while layout.count():
                child = layout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()
        
        # Limpa qualquer TreeView de variáveis se existir
        if hasattr(self, 'treeView'):
            self.treeView.setModel(None)
        
        log_action('analysis_state_reset')
    
    def _on_iniciar_analise_clicked(self):
        """Handler para botão Iniciar Análise."""
        if not self.note_data:
            QMessageBox.warning(self, "Aviso", "Selecione uma nota para análise.")
            return

        if self.analysis_in_progress:
            QMessageBox.warning(self, "Aviso", "Análise já em andamento.")
            return

        note_id = str(self.note_data.get("NR_ATIVIDADE", ""))
        if self.lock_manager and not self.lock_manager.is_note_locked_by_me(note_id):
            QMessageBox.warning(
                self,
                "Erro de Bloqueio",
                "Esta nota não está bloqueada para você.\n"
                "Volte à tela inicial e selecione a nota novamente."
            )
            return

        # 1) Início de processo
        self.analysis_in_progress = True
        self.btn_iniciar_analise.setEnabled(False)
        self.btn_abrir_anexos.setEnabled(True)
        self.txt_results.clear()
        self.progress_bar.setValue(0)
        self.lbl_status.setText("Iniciando análise…")

        # 2) Timer e métricas
        metrics_manager.start_analysis_timer(note_id)
        metrics_manager.record_analysis_step(note_id, "iniciar_analise")

        # 3) Monta o combined_data
        combined_data = {}
        # dados do HANA
        combined_data.update(self.uc_data)
        # dados da nota (Oracle)
        combined_data.update(self.note_data)

        # injeta campos do site (se disponíveis)
        if hasattr(self, 'valores_site'):
            combined_data.update(self.valores_site)
        else:
            # defaults, só para garantir que não falhe o .format na árvore
            defaults = {
                "qnt_mod_site": "Valor não encontrado, favor verificar",
                "qnt_inv_site": "Valor não encontrado, favor verificar",
                "potencia_total_mod_site": "Valor não encontrado, favor verificar",
                "modelo_mod_site": "Valor não encontrado, favor verificar",
                "modelo_inv_site": "Valor não encontrado, favor verificar",
                "potencia_total_inv_site": "Valor não encontrado, favor verificar",
                "menor_potencia_site": "Valor não encontrado, favor verificar",
                "campo_profissional_site": "Valor não encontrado, favor verificar",
                "proprietario_site": "Valor não encontrado, favor verificar",
            }
            combined_data.update(defaults)

        # pasta de anexos, se existir
        if hasattr(self, 'downloads_folder') and self.downloads_folder:
            combined_data["downloads_folder"] = self.downloads_folder

        # 4) Injeta no DecisionTree e dispara a análise
        self.decision_tree.set_data(combined_data)
        self._run_decision_tree()
        log_action('analysis_started', {'nr_atividade': note_id})
        
    def start_analysis(self):
        """
        Programmatic entry point to exactly the same logic as
        clicking the 'Iniciar Análise' button.
        """
        # simply defer to the existing handler
        self._on_iniciar_analise_clicked()
        
    def atualizar_treeview_com_valores(self):
        model = QStandardItemModel()
        model.setHorizontalHeaderLabels(['Variável', 'Valor'])
        
        # Verifica se valores_site existe antes de usá-lo
        if hasattr(self, 'valores_site') and self.valores_site:
            for chave, valor in self.valores_site.items():
                item_var   = QStandardItem(chave)
                item_valor = QStandardItem(str(valor))
                model.appendRow([item_var, item_valor])
        else:
            # Adiciona uma linha informando que não há dados
            item_var   = QStandardItem("Nenhum dado disponível")
            item_valor = QStandardItem("Faça o download dos anexos primeiro")
            model.appendRow([item_var, item_valor])
            
        self.treeView.setModel(model)
        self.treeView.expandAll()
    

    
    def _run_decision_tree(self):
        """Executa a árvore de decisão em uma thread separada."""
        try:
            # Atualiza a interface
            self._update_status("Executando árvore de decisão...")
            
            self.decision_tree.note_id = str(self.note_data.get("NR_ATIVIDADE"))
            self.decision_tree.user_id = os.getlogin()            
            # Executa a árvore de decisão
            history, pendencias = self.decision_tree.run_tree()
            
            # Atualiza a interface com os resultados
            self._update_status("Análise concluída")
            self._update_progress(100)
            
            # Chama diretamente o método de conclusão da análise
            # Em vez de depender do sinal
            self._on_analysis_completed()
            
            # Registra o passo de análise
            note_id = str(self.note_data.get("NR_ATIVIDADE", ""))
            metrics_manager.record_analysis_step(note_id, "decision_tree_completed")
            
            log_action('decision_tree_completed', {
                'nr_atividade': note_id,
                'history_count': len(history),
                'pendencias_count': len(pendencias)
            })
            
        except Exception as e:
            # Em caso de erro, exibe mensagem e registra
            import traceback
            error_msg = f"Erro ao executar árvore de decisão: {str(e)}\n{traceback.format_exc()}"
            self._update_status(f"Erro: {str(e)}")
            
            log_action('decision_tree_error', {
                'error': str(e)
            })
            
            # Exibe mensagem de erro
            QMessageBox.critical(
                self,
                "Erro na Análise",
                f"Ocorreu um erro ao executar a análise:\n{str(e)}"
            )
            
            # Finaliza a análise
            self.analysis_in_progress = False
            self.btn_iniciar_analise.setEnabled(True)
    
    def _on_analysis_completed(self):
        """Handler para sinal de análise concluída."""
        # Finaliza o timer de análise
        note_id = str(self.note_data.get("NR_ATIVIDADE", ""))
        metrics_manager.end_analysis_timer(note_id, success=True)
        
        # Atualiza a interface
        self._update_status("Análise concluída")
        self._update_progress(100)
        
        # Exibe resumo das respostas
        self._show_analysis_summary()
        
        # Habilita botões
        self.analysis_in_progress = False
        self.btn_iniciar_analise.setEnabled(True)
        self.btn_abrir_anexos.setEnabled(True)
        # self.btn_gerar_parecer.setEnabled(True)
        
        log_action('analysis_completed', {
            'nr_atividade': note_id
        })
    
    def _show_analysis_summary(self):
        """Exibe um resumo da análise."""
        history = self.decision_tree.get_history()
        pendencias = self.decision_tree.get_pendencias()
        active_flags = self.flags_manager.get_active_flags()
        
        summary = "=== RESUMO DA ANÁLISE ===\n\n"
        
        # Adiciona respostas
        summary += "RESPOSTAS:\n"
        for key, value in history.items():
            if isinstance(value, list):
                summary += f"- {key}: {', '.join(value)}\n"
            else:
                summary += f"- {key}: {value}\n"
        
        # Adiciona pendências
        if pendencias:
            summary += "\nPENDÊNCIAS IDENTIFICADAS:\n"
            for p in pendencias:
                summary += f"- {p}\n"
        
        # Adiciona flags ativas
        if active_flags:
            summary += "\nFLAGS ATIVAS:\n"
            for flag, value in active_flags.items():
                summary += f"- {flag}: {value}\n"
        
        # Exibe o resumo
        self.txt_results.setText(summary)
    
    def _on_abrir_anexos_clicked(self):
        """Handler para botão Abrir Pasta de Anexos."""
        if self.downloads_folder and os.path.exists(self.downloads_folder):
            os.startfile(self.downloads_folder)
            log_action('open_attachments_folder', {
                'folder': self.downloads_folder
            })
        else:
            QMessageBox.warning(
                self,
                "Aviso",
                "Pasta de anexos não encontrada.\n"
                "Verifique se os anexos foram baixados."
            )
    def _build_report(self, nota, uc_data, with_deadline, days):
        
        """Handler para botão Gerar Parecer."""
        if not self.note_data:
            QMessageBox.warning(self, "Aviso", "Selecione uma nota para análise.")
            return
        
        metrics_manager.start_stage(str(nota), "generate_report")        
        # Adiciona log para depuração das flags ativas
        active_flags = self.flags_manager.get_active_flags()
        log_action('debug_active_flags_before_report', {
            'active_flags': str(active_flags),
            'count': len(active_flags)
        })
        
        dt = self.analysis_form.decision_tree
        log_action('debug_dt_history', {'history': dt.history})
        fast_opt = dt.history.get("fast_track", "não")
        # Salva na nota selecionada (self.note_data), não em uma variável inexistente:
        self.note_data["fast_track"] = fast_opt
        
        # Gera o parecer com os argumentos corretos
        report_text = self.report_generator.generate_report(
            nota_info=self.note_data,
             uc_info=self.uc_data,
             prazo=7
         )
        
        # Verifica se há flags ativas que causam indeferimento
        has_indeferimento = False
        if self.flags_manager:
            for flag_id, value in self.flags_manager.get_active_flags().items():
                if flag_id not in ['flag_91_sim', 'flag_91_nao'] and value:
                    has_indeferimento = True
                    log_action('flag_causing_indeferimento', {
                        'flag_id': flag_id,
                        'value': value
                    })
                    break
        
        # Determina o status com base nas flags
        status = "indeferido" if has_indeferimento else "deferido"
        
        # Exibe o parecer (agora como string)
        self.txt_results.setText(report_text)
        
        # Registra a geração do parecer
        note_id = str(self.note_data.get("NR_ATIVIDADE", ""))
        metrics_manager.record_analysis_step(note_id, "report_generated")
        
        log_action('report_generated', {
            'nr_atividade': note_id,
            'status': status,
            'deferido': not has_indeferimento
        })
        
        # Exibe mensagem de conclusão
        QMessageBox.information(
            self,
            "Parecer Gerado",
            f"Parecer gerado com sucesso.\n\n"
            f"Status: {status.upper()}"
        )
        
        report_text = self.report_generator.generate_report(
            nota_info=nota,
            uc_info=uc_data,
            prazo=days if with_deadline else 0  # ou seu próprio critério
        )
        
        # retorne a variável correta:
        return report_text
    def _on_gerar_parecer_clicked(self):
        report = self._build_report(
            self.note_data,
            self.uc_data,
            self.results_view.chk_with_deadline.isChecked(),
            self.results_view.spn_deadline_days.value()
        )
        if report:
            self.results_view.set_report_text(report)

    def set_downloads_folder(self, folder: str):
        self.downloads_folder = folder
        self.btn_abrir_anexos.setEnabled(os.path.exists(folder))
        # Atualiza a lista de anexos:
        self.populate_attachments(folder)
        log_action('downloads_folder_set', {'folder': folder})
    
    def _update_status(self, status):
        """
        Atualiza o status na interface.
        
        Args:
            status (str): Texto de status.
        """
        # Executa na thread da UI
        from PyQt5.QtCore import QMetaObject, Qt, Q_ARG
        QMetaObject.invokeMethod(
            self.lbl_status,
            "setText",
            Qt.QueuedConnection,
            Q_ARG(str, status)
        )
    
    def _update_progress(self, value):
        """
        Atualiza a barra de progresso.
        
        Args:
            value (int): Valor do progresso (0-100).
        """
        # Executa na thread da UI
        from PyQt5.QtCore import QMetaObject, Qt, Q_ARG
        QMetaObject.invokeMethod(
            self.progress_bar,
            "setValue",
            Qt.QueuedConnection,
            Q_ARG(int, value)
        )
    
    # def _enable_generate_report(self):
    #     """Habilita o botão de gerar parecer."""
    #     # Executa na thread da UI
    #     from PyQt5.QtCore import QMetaObject, Qt, Q_ARG
    #     QMetaObject.invokeMethod(
    #         self.btn_gerar_parecer,
    #         "setEnabled",
    #         Qt.QueuedConnection,
    #         Q_ARG(bool, True)
    #     )
