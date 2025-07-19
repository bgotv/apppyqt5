"""
Módulo de interface gráfica - Visualização de resultados.
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTextEdit, QCheckBox, QSpinBox, QGroupBox, QFormLayout,
    QApplication
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont

from app.utils.logger import log_ui_action
from app.utils.performance import PerformanceTracker


class ResultsView(QWidget):
    """
    Widget para visualização de resultados e pareceres.
    """
    # Sinais
    report_generated = pyqtSignal(str)  # report_text
    
    def __init__(self):
        """Inicializa a visualização de resultados."""
        super().__init__()
        
        # Inicializa a interface
        self._init_ui()
        
        # Registra a inicialização
        log_ui_action('results_view_initialized')
    
    def _init_ui(self):
        """Inicializa os componentes da interface."""
        # Layout principal
        main_layout = QVBoxLayout(self)
        
        # Opções de geração
        options_group = QGroupBox("Opções de Geração")
        options_layout = QFormLayout()
        
        self.chk_with_deadline = QCheckBox("Incluir prazo")
        self.chk_with_deadline.setChecked(False)
        options_layout.addRow(self.chk_with_deadline, QLabel())
        
        self.spn_deadline_days = QSpinBox()
        self.spn_deadline_days.setMinimum(1)
        self.spn_deadline_days.setMaximum(30)
        self.spn_deadline_days.setValue(7)
        self.spn_deadline_days.setEnabled(False)        # desabilita até que seja marcado
        options_layout.addRow("Prazo (dias):", self.spn_deadline_days)
        
        options_group.setLayout(options_layout)
        main_layout.addWidget(options_group)
        
        # Área de texto para o parecer
        self.txt_report = QTextEdit()
        self.txt_report.setReadOnly(True)
        self.txt_report.setFont(QFont("Consolas", 10))
        main_layout.addWidget(self.txt_report)
        
        # Conecta eventos
        self.chk_with_deadline.toggled.connect(self._on_deadline_toggled)
    
    def set_report_text(self, text):
        """
        Define o texto do parecer.
        
        Args:
            text (str): Texto do parecer.
        """
        with PerformanceTracker("set_report_text_ui") as tracker:
            self.txt_report.setPlainText(text)
            tracker.add_detail("text_length", len(text))
            log_ui_action('report_text_set', {'text_length': len(text)})
            
            # Emite o sinal
            self.report_generated.emit(text)
    
    def get_report_text(self):
        """
        Obtém o texto do parecer.
        
        Returns:
            str: Texto do parecer.
        """
        return self.txt_report.toPlainText()
    
    def get_deadline_options(self):
        """
        Obtém as opções de prazo.
        
        Returns:
            dict: Dicionário com as opções de prazo.
        """
        return {
            'with_deadline': self.chk_with_deadline.isChecked(),
            'deadline_days': self.spn_deadline_days.value()
        }
    
    def copy_to_clipboard(self):
        """Copia o texto do parecer para a área de transferência."""
        text = self.txt_report.toPlainText()
        QApplication.clipboard().setText(text)
        log_ui_action('report_copied_to_clipboard', {'text_length': len(text)})
    
    def _on_deadline_toggled(self, checked):
        """
        Handler para alteração do checkbox de prazo.
        
        Args:
            checked (bool): Estado do checkbox.
        """
        self.spn_deadline_days.setEnabled(checked)
        log_ui_action('deadline_toggled', {'checked': checked})
