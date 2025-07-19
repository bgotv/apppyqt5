# app/ui/filters_integration.py
from PyQt5.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QComboBox, QDateEdit
)
from PyQt5.QtCore import pyqtSlot, QDate
from app.utils.status_calculator import calcular_status
import re

# def adicionar_filtros_a_main_window(self):
#     """Cria e retorna um QFrame contendo todos os filtros."""
#     filtro_frame = QFrame()
#     filtro_layout = QVBoxLayout(filtro_frame)
#     filtro_frame.setFrameShape(QFrame.StyledPanel)

#     # Título
#     filtro_titulo = QLabel("Filtros")
#     filtro_titulo.setStyleSheet("font-weight: bold;")
#     filtro_layout.addWidget(filtro_titulo)

#     # Linha 1: número + status
#     linha1 = QHBoxLayout()
#     linha1.addWidget(QLabel("Número:"))
#     self.filtro_entry = QLineEdit()
#     self.filtro_entry.setMaximumWidth(150)
#     self.filtro_entry.textChanged.connect(self._on_filtro_changed)
#     linha1.addWidget(self.filtro_entry)

#     linha1.addWidget(QLabel("Status:"))
#     self.status_combobox = QComboBox()
#     self.status_combobox.addItems(["", "D0","D1","D2","D3","D4","D5","D6","D7+"])
#     self.status_combobox.setMaximumWidth(100)
#     self.status_combobox.currentTextChanged.connect(self._on_filtro_changed)
#     linha1.addWidget(self.status_combobox)

#     filtro_layout.addLayout(linha1)

#     # Linha 2: Comercial, Técnica, Resp. Projeto
#     linha2 = QHBoxLayout()
#     linha2.addWidget(QLabel("Comercial:"))
#     self.filtro_com_combobox = QComboBox()
#     self.filtro_com_combobox.addItems(["","Sim","Não"])
#     self.filtro_com_combobox.setMaximumWidth(100)
#     self.filtro_com_combobox.currentTextChanged.connect(self._on_filtro_changed)
#     linha2.addWidget(self.filtro_com_combobox)

#     linha2.addWidget(QLabel("Técnica:"))
#     self.filtro_tec_combobox = QComboBox()
#     self.filtro_tec_combobox.addItems(["","Sim","Não"])
#     self.filtro_tec_combobox.setMaximumWidth(100)
#     self.filtro_tec_combobox.currentTextChanged.connect(self._on_filtro_changed)
#     linha2.addWidget(self.filtro_tec_combobox)

#     linha2.addWidget(QLabel("Resp. Projeto:"))
#     self.filtro_resp_combobox = QComboBox()
#     self.filtro_resp_combobox.addItems(["","GA","O&M"])
#     self.filtro_resp_combobox.setMaximumWidth(100)
#     self.filtro_resp_combobox.currentTextChanged.connect(self._on_filtro_changed)
#     linha2.addWidget(self.filtro_resp_combobox)

#     filtro_layout.addLayout(linha2)

#     # Linha 3: Data início, Data fim
#     linha3 = QHBoxLayout()
#     linha3.addWidget(QLabel("Período:"))
#     self.data_inicio = QDateEdit(calendarPopup=True)
#     self.data_inicio.setDate(QDate.currentDate().addMonths(-1))
#     self.data_inicio.dateChanged.connect(self._on_filtro_changed)
#     linha3.addWidget(self.data_inicio)
#     linha3.addWidget(QLabel("até"))
#     self.data_fim = QDateEdit(calendarPopup=True)
#     self.data_fim.setDate(QDate.currentDate())
#     self.data_fim.dateChanged.connect(self._on_filtro_changed)
#     linha3.addWidget(self.data_fim)

#     filtro_layout.addLayout(linha3)

#     return filtro_frame

# @pyqtSlot()
# def _on_filtro_changed(self):
#     """
#     Slot que filtra self.all_notes conforme os controles.
#     """
#     notas_base = getattr(self, 'all_notes', [])
#     num    = self.filtro_entry.text().strip()
#     status = self.status_combobox.currentText().strip().upper()
#     com    = self.filtro_com_combobox.currentText().strip().lower()
#     tec    = self.filtro_tec_combobox.currentText().strip().lower()
#     resp   = self.filtro_resp_combobox.currentText().strip().lower()

#     filtradas = []
#     for note in notas_base:
#         nota_str  = str(note.get("NR_ATIVIDADE",""))
#         agu_com   = str(note.get("AGUARDA_ANALISE_COMERCIAL","")).lower()
#         agu_tec   = str(note.get("AGUARDA_ANALISE_TECNICA","")).lower()
#         resp_proj = str(note.get("PROJ_RESP","")).lower()
#         data_cad  = note.get("DT_CADASTRO","")
#         stat      = calcular_status(data_cad)

#         cond_num  = (num in nota_str) if num else True

#         if status:
#             if status != "D7+":
#                 cond_stat = (stat == status)
#             else:
#                 m = re.match(r'^D(\d+)\+?$', stat)
#                 cond_stat = bool(m and int(m.group(1)) >= 7)
#         else:
#             cond_stat = True

#         cond_com  = (agu_com == com) if com else True
#         cond_tec  = (agu_tec == tec) if tec else True
#         cond_resp = (resp_proj == resp) if resp else True

#         if cond_num and cond_stat and cond_com and cond_tec and cond_resp:
#             filtradas.append(note)

#     self.tree_notas.set_notes(filtradas)

