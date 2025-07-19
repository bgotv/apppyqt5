# app/ui/notes_lock_view.py

import pandas as pd
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTreeWidget, QTreeWidgetItem, QHeaderView, QMessageBox
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QColor, QBrush

from app.core.note_lock_manager import NoteLockManager
from app.utils.logger import log_ui_action
from app.utils.performance import PerformanceTracker
from app.utils.status_calculator import calcular_status
from app.utils.status_calculator import calcular_tipo_projeto
from PyQt5.QtCore import QDateTime


class CustomTreeWidgetItem(QTreeWidgetItem):
    def __lt__(self, other):
        column = self.treeWidget().sortColumn()
        if column == 3:  # Data Cadastro
            self_date = self.data(column, Qt.UserRole)
            other_date = other.data(column, Qt.UserRole)
            return self_date < other_date
        return super().__lt__(other)


class NotesTreeView(QTreeWidget):
    """
    Widget de árvore para visualização de notas técnicas com suporte a bloqueio.
    """
    note_selected = pyqtSignal(dict)

    def __init__(self, lock_manager=None):
        super().__init__()
        self.lock_manager = lock_manager or NoteLockManager()

        # Configurações da árvore
        headers = ["Atividade", "UC", "Cliente", "Data Cadastro", "Status", "Tipo", "Tipo Projeto", "Bloqueio"]
        self.setHeaderLabels(headers)
        self.header().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.setAlternatingRowColors(True)
        self.setSelectionMode(QTreeWidget.SingleSelection)
        # Permite bloquear/desbloquear com duplo clique
        self.itemDoubleClicked.connect(self._on_item_double_clicked)

        # Cores para itens bloqueados
        self.locked_by_me_color     = QColor(200, 255, 200)  # verde claro
        self.locked_by_others_color = QColor(255, 200, 200)  # vermelho claro

        # Lista interna de notas
        self.notes = []

    def set_notes(self, notes):
        """
        Recebe a lista de notas vindas do Oracle e atualiza a árvore.
        Chamado por filtros e pela consulta inicial.
        Garante que não haja atividades duplicadas.
        """
        with PerformanceTracker("set_notes_ui") as tracker:
            seen = set()
            unique_notes = []
            for note in notes:
                atividade = note.get("NR_ATIVIDADE")
                if atividade not in seen:
                    seen.add(atividade)
                    unique_notes.append(note)

            # atribui a lista sem duplicados
            self.notes = unique_notes
            self._update_tree()
            tracker.add_detail("notes_count", len(self.notes))
            
    def calcular_tipo_projeto(data_parecer, data_cadastro, cd_status):
        try:
            d1 = pd.to_datetime(data_parecer, dayfirst=True).normalize()
            d2 = pd.to_datetime(data_cadastro, dayfirst=True).normalize()
            if d1 == d2:
                return "Novo Projeto"
            if d1 != d2 and cd_status == 224:
                return "No Inbox"
            if d1 != d2 and cd_status != 224:
                return "Reanálise"
        except Exception:
            pass
        return "Indefinido"
    

    def _update_tree(self):
        """
        Reconstrói completamente a árvore a partir de self.notes,
        pintando as linhas que estejam bloqueadas.
        """
        self.clear()
        locked = self.lock_manager.get_locked_notes()

        for idx, note in enumerate(self.notes):
            atividade     = str(note.get('NR_ATIVIDADE', ''))
            uc            = str(note.get('CD_UC', ''))
            cliente       = note.get('NOME_RAZAO', '—')
            data_cadastro = str(note.get('DT_CADASTRO', ''))
            status        = calcular_status(data_cadastro) or "Aguardando Análise"
            tipo          = str(note.get('tipo', 'GD'))
            tipo_projeto  = calcular_tipo_projeto(
                note.get("DT_PARECER"),
                note.get("DT_CADASTRO"),
                note.get("CD_STATUS")
            )
            bloqueio_txt  = ""

            item = CustomTreeWidgetItem([
                atividade,
                uc,
                cliente,
                data_cadastro,
                status,
                tipo,
                tipo_projeto,
                bloqueio_txt
            ])
            item.setData(0, Qt.UserRole, atividade)

            # Armazena data como QDateTime para ordenação real
            try:
                dt = pd.to_datetime(data_cadastro, dayfirst=True)
                item.setData(3, Qt.UserRole, QDateTime(dt.to_pydatetime()))
            except:
                item.setData(3, Qt.UserRole, QDateTime())  # vazio

            # Se bloqueada, pinta em cores e mostra quem bloqueou
            info = locked.get(atividade)
            if info:
                bloqueio_txt = f"Bloqueado por {info['user']}"
                item.setText(6, bloqueio_txt)

                color = (self.locked_by_me_color
                         if info['user'] == self.lock_manager.current_user
                         else self.locked_by_others_color)
                for col in range(item.columnCount()):
                    item.setBackground(col, QBrush(color))

            self.addTopLevelItem(item)
        self.sortItems(3, Qt.AscendingOrder)

    def get_selected_note(self):
        """
        Retorna o dicionário da nota selecionada, ou None se nada estiver selecionado.
        Usa o número da atividade (NR_ATIVIDADE) como chave segura.
        """
        items = self.selectedItems()
        if not items:
            return None

        item = items[0]
        atividade = item.data(0, Qt.UserRole)

        if not atividade:
            return None

        for note in self.notes:
            if str(note.get("NR_ATIVIDADE", "")).strip() == str(atividade).strip():
                return note

        return None

    def lock_selected_note(self) -> bool:
        """
        Tenta bloquear a nota atualmente selecionada.
        Retorna True em caso de sucesso (ou se já estiver bloqueada por você).
        """
        note = self.get_selected_note()
        if not note:
            return False

        activity_id = str(note.get('NR_ATIVIDADE', ''))
        # Se já bloqueada por mim, está tudo certo
        if self.lock_manager.is_note_locked_by_me(activity_id):
            return True

        success = self.lock_manager.lock_note(activity_id)
        if success:
            self._update_tree()
            self.note_selected.emit(note)
            log_ui_action('note_locked_ui', {'note_id': activity_id})
            return True

        return False

    def unlock_selected_note(self) -> bool:
        """
        Tenta desbloquear a nota atualmente selecionada.
        Retorna True em caso de sucesso.
        """
        note = self.get_selected_note()
        if not note:
            return False

        activity_id = str(note.get('NR_ATIVIDADE', ''))
        success = self.lock_manager.unlock_note(activity_id)
        if success:
            self._update_tree()
            log_ui_action('note_unlocked_ui', {'note_id': activity_id})
            return True

        return False

    def unlock_all_my_notes(self) -> int:
        """
        Desbloqueia todas as notas que eu tenha bloqueado.
        Retorna o número de notas desbloqueadas.
        """
        count = self.lock_manager.unlock_all_my_notes()
        if count:
            self._update_tree()
            log_ui_action('notes_unlocked_all_ui', {'count': count})
        return count

    def _on_item_double_clicked(self, item, column):
        """
        Duplo clique no item => tenta bloquear (ou desbloquear, conforme sua lógica).
        Aqui só chamamos o lock.
        """
        self.lock_selected_note()


class NotesLockPanel(QWidget):
    """
    Painel com botões para bloquear/desbloquear notas individuais ou todas de uma vez.
    """
    def __init__(self, notes_tree=None):
        super().__init__()
        self.notes_tree = notes_tree
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        title = QLabel("Gerenciamento de Bloqueio")
        title.setFont(QFont("Arial", 11, QFont.Bold))
        layout.addWidget(title)

        # Legenda de cores
        legend = QWidget()
        legend_layout = QHBoxLayout(legend)
        for text, col in [
            ("Bloqueado por você", "#c8ffc8"),
            ("Bloqueado por outros", "#ffc8c8")
        ]:
            sw = QWidget()
            sw.setFixedSize(16, 16)
            sw.setStyleSheet(f"background-color: {col}; border: 1px solid #888;")
            legend_layout.addWidget(sw)
            legend_layout.addWidget(QLabel(text))
            legend_layout.addSpacing(20)
        legend_layout.addStretch()
        layout.addWidget(legend)

        # Botões
        btns = QHBoxLayout()
        btns.addWidget(QPushButton("Bloquear Nota", clicked=self._on_lock_clicked))
        btns.addWidget(QPushButton("Desbloquear Nota", clicked=self._on_unlock_clicked))
        btns.addWidget(QPushButton("Desbloquear Todas", clicked=self._on_unlock_all_clicked))
        layout.addLayout(btns)

    def _on_lock_clicked(self):
        if self.notes_tree and not self.notes_tree.lock_selected_note():
            QMessageBox.warning(self, "Erro", "Não foi possível bloquear a nota.")

    def _on_unlock_clicked(self):
        if self.notes_tree and not self.notes_tree.unlock_selected_note():
            QMessageBox.warning(self, "Erro", "Não foi possível desbloquear a nota.")

    def _on_unlock_all_clicked(self):
        if not self.notes_tree:
            return
        resposta = QMessageBox.question(
            self, "Confirmar",
            "Desbloquear todas as suas notas?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if resposta == QMessageBox.Yes:
            cnt = self.notes_tree.unlock_all_my_notes()
            QMessageBox.information(self, "Feito", f"{cnt} nota(s) desbloqueada(s).")
