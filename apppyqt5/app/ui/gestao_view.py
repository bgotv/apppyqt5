""" 
Módulo para implementação da aba de gestão com visão gerencial.
Este código deve ser integrado à classe MainWindow no arquivo main_window.py.
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTabWidget, QTableWidget, 
    QTableWidgetItem, QHeaderView, QSplitter, QFrame, QComboBox, QPushButton,
    QDateEdit, QGroupBox, QProgressBar, QGridLayout, QSpacerItem, QSizePolicy
)
from PyQt5.QtCore import Qt, QDate, pyqtSlot
from PyQt5.QtGui import QColor, QBrush, QPainter, QPen, QFont, QPixmap, QIcon
from PyQt5.QtChart import QChart, QChartView, QPieSeries, QBarSeries, QBarSet, QBarCategoryAxis, QValueAxis

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random # Para dados de exemplo
from app.utils.status_calculator import calcular_status
from datetime import datetime

# Classe para a aba de gestão
class GestaoView(QWidget):
    """
    Widget para visualização de dados gerenciais.
    """
    def __init__(self, parent=None):
        """
        Inicializa a visualização de gestão.
        
        Args:
            parent (QWidget, optional): Widget pai.
        """
        
        super().__init__(parent)
        # vai guardar o dataset real que chegará do MainWindow
        self._all_notes = []    # guardará todo o dataset
        self.notes_data = []    # guardará apenas o filtrado
        # inicializa a interface
        self._init_ui()
        
    def _init_ui(self):
        """Inicializa os componentes da interface."""
        # Layout principal
        main_layout = QVBoxLayout(self)
        
        # Título com indicadores de status
        header_layout = QHBoxLayout()
        
        title_label = QLabel("📊 Painel de Gestão")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #2c3e50;
                padding: 10px;
            }
        """)
        header_layout.addWidget(title_label)
        
        # Indicadores rápidos
        self.total_label = QLabel("📋 Total: 0")
        self.pendentes_label = QLabel("⏳ Pendentes: 0")
        self.atrasadas_label = QLabel("🚨 Atrasadas: 0")
        
        for label in [self.total_label, self.pendentes_label, self.atrasadas_label]:
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
            header_layout.addWidget(label)
        
        header_layout.addStretch()
        main_layout.addLayout(header_layout)
        
        # Seção de filtros
        filtros_group = QGroupBox("🔍 Filtros")
        filtros_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #3498db;
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
        filtros_layout = QHBoxLayout(filtros_group)
        
        # Data início
        filtros_layout.addWidget(QLabel("📅 De:"))
        self.data_inicio = QDateEdit()
        self.data_inicio.setDate(QDate.currentDate().addDays(-30))
        self.data_inicio.setCalendarPopup(True)
        filtros_layout.addWidget(self.data_inicio)
        
        # Data fim
        filtros_layout.addWidget(QLabel("📅 Até:"))
        self.data_fim = QDateEdit()
        self.data_fim.setDate(QDate.currentDate())
        self.data_fim.setCalendarPopup(True)
        filtros_layout.addWidget(self.data_fim)
        
        # Área
        filtros_layout.addWidget(QLabel("🏢 Área:"))
        self.area_combobox = QComboBox()
        self.area_combobox.addItems(["Todas", "Área 1", "Área 2", "Área 3"])
        filtros_layout.addWidget(self.area_combobox)
        
        # Botão de atualizar
        self.btn_atualizar = QPushButton("🔄 Atualizar Dados")
        self.btn_atualizar.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #21618c;
            }
        """)
        self.btn_atualizar.clicked.connect(self._atualizar_dados)
        filtros_layout.addWidget(self.btn_atualizar)
        
        filtros_layout.addStretch()
        main_layout.addWidget(filtros_group)
        
        # Splitter para dividir gráficos e tabelas
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter, stretch=1)
        
        # Painel esquerdo - Gráficos
        graficos_widget = QWidget()
        graficos_layout = QVBoxLayout(graficos_widget)
        
        # Gráfico de pizza
        graficos_layout.addWidget(QLabel("📊 Distribuição por Status"))
        self.pie_chart_view = self._criar_grafico_pizza()
        graficos_layout.addWidget(self.pie_chart_view, stretch=1)
        
        # Gráfico de barras
        graficos_layout.addWidget(QLabel("📈 Atividades por Área"))
        self.bar_chart_view = self._criar_grafico_barras()
        graficos_layout.addWidget(self.bar_chart_view, stretch=1)
        
        splitter.addWidget(graficos_widget)
        
        # Painel direito - Tabelas
        tabelas_widget = QTabWidget()
        tabelas_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #bdc3c7;
                border-radius: 5px;
            }
            QTabBar::tab {
                background-color: #ecf0f1;
                padding: 8px 12px;
                margin-right: 2px;
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
            }
            QTabBar::tab:selected {
                background-color: #3498db;
                color: white;
            }
        """)
        
        # Tab de resumo por status
        self.tab_resumo_status = QWidget()
        self._init_tab_resumo_status()
        tabelas_widget.addTab(self.tab_resumo_status, "📊 Status")
        
        # Tab de resumo por área
        self.tab_resumo_area = QWidget()
        self._init_tab_resumo_area()
        tabelas_widget.addTab(self.tab_resumo_area, "🏢 Áreas")
        
        # Tab de produtividade
        self.tab_produtividade = QWidget()
        self._init_tab_produtividade()
        tabelas_widget.addTab(self.tab_produtividade, "👥 Produtividade")
        
        splitter.addWidget(tabelas_widget)
        
        # Define proporções do splitter
        splitter.setSizes([400, 600])
        
        # Conecta eventos dos filtros
        self.data_inicio.dateChanged.connect(self._atualizar_dados)
        self.data_fim.dateChanged.connect(self._atualizar_dados)
        self.area_combobox.currentTextChanged.connect(self._atualizar_dados)
        
    def set_notes_data(self, notes):
        """Recebe o dataset real e força atualização."""
        self._all_notes = notes or []
        self._atualizar_dados()  # Unifica em um só método
        
    def _atualizar_indicadores_rapidos(self):
        """Atualiza os indicadores rápidos no topo da tela."""
        total = len(self.notes_data)
        
        # Conta pendentes e atrasadas
        pendentes = 0
        atrasadas = 0
        
        for note in self.notes_data:
            status = calcular_status(note.get("DT_CADASTRO", "")) or "Aguardando Análise"
            if "D7+" in status or "Atrasada" in status:
                atrasadas += 1
            elif not note.get("DT_PARECER"):
                pendentes += 1
        
        # Atualiza labels com cores
        self.total_label.setText(f"📋 Total: {total}")
        
        self.pendentes_label.setText(f"⏳ Pendentes: {pendentes}")
        if pendentes > total * 0.7:  # Mais de 70% pendentes
            self.pendentes_label.setStyleSheet("""
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
        else:
            self.pendentes_label.setStyleSheet("""
                QLabel {
                    background-color: #ecf0f1;
                    border: 1px solid #bdc3c7;
                    border-radius: 5px;
                    padding: 8px;
                    margin: 2px;
                    font-weight: bold;
                }
            """)
        
        self.atrasadas_label.setText(f"🚨 Atrasadas: {atrasadas}")
        if atrasadas > 0:
            self.atrasadas_label.setStyleSheet("""
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
        else:
            self.atrasadas_label.setStyleSheet("""
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

    @pyqtSlot()
    def _atualizar_dados(self):
        """Método único para atualizar todos os dados e visualizações."""
        # Filtra por período
        inicio = self.data_inicio.date().toPyDate()
        fim = self.data_fim.date().toPyDate()
        area_sel = self.area_combobox.currentText()
        
        # Aplica filtros SEM duplicar dados
        filtered = []
        for n in self._all_notes:
            # converte DT_CADASTRO
            try:
                d = datetime.strptime(n.get("DT_CADASTRO", ""), "%d-%m-%y").date()
            except:
                continue
            if not (inicio <= d <= fim):
                continue
            if area_sel != "Todas" and n.get("PROJ_RESP", "") != area_sel:
                continue
            filtered.append(n)
        
        # CORREÇÃO: Define notes_data uma única vez
        self.notes_data = filtered
        
        # Atualiza indicadores rápidos
        self._atualizar_indicadores_rapidos()
        
        # 1) Conta por status
        status_counts = {}
        for note in self.notes_data:
            st = calcular_status(note.get("DT_CADASTRO", "")) or "Aguardando Análise"
            status_counts[st] = status_counts.get(st, 0) + 1

        # 2) Conta por área
        area_counts = {}
        for note in self.notes_data:
            area = note.get("PROJ_RESP", "Desconhecido")
            area_counts[area] = area_counts.get(area, 0) + 1

        # 3) Calcula produtividade por usuário
        user_stats = {}
        for note in self.notes_data:
            user = note.get("USER_NAME") or note.get("CD_USUARIO_EXTERNO") or "Desconhecido"
            # inicializa
            if user not in user_stats:
                user_stats[user] = {
                    "concluidas": 0,
                    "total_time_days": 0,
                    "em_andamento": 0
                }
            # verifica se já tem parecer
            dt_parecer = note.get("DT_PARECER")
            # DT_CADASTRO vem como string "dd-mm-yy"
            cad = note.get("DT_CADASTRO")
            try:
                cad_dt = datetime.strptime(cad, "%d-%m-%y")
            except:
                cad_dt = None

            if dt_parecer and cad_dt:
                user_stats[user]["concluidas"] += 1
                # dt_parecer pode ser datetime ou string
                pr = dt_parecer
                if isinstance(pr, str):
                    try:
                        pr = datetime.strptime(pr, "%d-%m-%y")
                    except:
                        pr = None
                if isinstance(pr, datetime):
                    delta = (pr - cad_dt).days
                    user_stats[user]["total_time_days"] += max(delta, 0)
            else:
                user_stats[user]["em_andamento"] += 1

        produtividade_data = []
        for user, stats in user_stats.items():
            c = stats["concluidas"]
            e = stats["em_andamento"]
            tm = (stats["total_time_days"] / c) if c > 0 else 0
            ef = (c / (c + e)) if (c + e) > 0 else 0
            produtividade_data.append({
                "usuario": user,
                "concluidas": c,
                "tempo_medio": round(tm, 1),
                "em_andamento": e,
                "eficiencia": round(ef, 2)
            })

        # 4) Atualiza todas as visualizações
        self._atualizar_grafico_pizza(status_counts)
        self._atualizar_grafico_barras(area_counts)
        self._atualizar_tabela_status(status_counts)
        self._atualizar_tabela_area(area_counts)
        self._atualizar_tabela_produtividade(produtividade_data)

    def _init_tab_resumo_status(self):
        """Inicializa a tab de resumo por status."""
        layout = QVBoxLayout(self.tab_resumo_status)
        
        # Tabela de resumo por status
        self.tabela_status = QTableWidget()
        self.tabela_status.setColumnCount(3)
        self.tabela_status.setHorizontalHeaderLabels(["Status", "Quantidade", "Percentual"])
        self.tabela_status.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.tabela_status)
    
    def _init_tab_resumo_area(self):
        """Inicializa a tab de resumo por área."""
        layout = QVBoxLayout(self.tab_resumo_area)
        
        # Tabela de resumo por área
        self.tabela_area = QTableWidget()
        self.tabela_area.setColumnCount(4)
        self.tabela_area.setHorizontalHeaderLabels(["Área", "Quantidade", "Percentual", "Tempo Médio (dias)"])
        self.tabela_area.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.tabela_area)
    
    def _init_tab_produtividade(self):
        """Inicializa a tab de produtividade."""
        layout = QVBoxLayout(self.tab_produtividade)
        
        # Tabela de produtividade
        self.tabela_produtividade = QTableWidget()
        self.tabela_produtividade.setColumnCount(5)
        self.tabela_produtividade.setHorizontalHeaderLabels([
            "Usuário", 
            "Atividades Concluídas", 
            "Tempo Médio (dias)",
            "Atividades em Andamento",
            "Eficiência"
        ])
        self.tabela_produtividade.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.tabela_produtividade)
    
    def _criar_grafico_pizza(self):
        """
        Cria um gráfico de pizza para atividades por status.
        
        Returns:
            QChartView: Visualização do gráfico.
        """
        # Cria a série de dados
        series = QPieSeries()
        
        # Cria o gráfico
        chart = QChart()
        chart.addSeries(series)
        chart.setTitle("Atividades por Status")
        chart.legend().setVisible(True)
        chart.legend().setAlignment(Qt.AlignBottom)
        
        # Cria a visualização do gráfico
        chart_view = QChartView(chart)
        chart_view.setRenderHint(QPainter.Antialiasing)
        
        return chart_view
    
    def _criar_grafico_barras(self):
        """
        Cria um gráfico de barras para atividades por área.
        
        Returns:
            QChartView: Visualização do gráfico.
        """
        # Cria a série de dados
        series = QBarSeries()
        
        # Cria o gráfico
        chart = QChart()
        chart.addSeries(series)
        chart.setTitle("Atividades por Área")
        chart.legend().setVisible(True)
        chart.legend().setAlignment(Qt.AlignBottom)
        
        # Cria os eixos
        axisX = QBarCategoryAxis()
        chart.addAxis(axisX, Qt.AlignBottom)
        series.attachAxis(axisX)
        
        axisY = QValueAxis()
        chart.addAxis(axisY, Qt.AlignLeft)
        series.attachAxis(axisY)
        
        # Cria a visualização do gráfico
        chart_view = QChartView(chart)
        chart_view.setRenderHint(QPainter.Antialiasing)
        
        return chart_view
    
    
    def _atualizar_grafico_pizza(self, status_data):
        """
        Atualiza o gráfico de pizza com os dados de status.
        
        Args:
            status_data (dict): Dicionário com os dados de status.
        """
        # Obtém o gráfico e a série
        chart = self.pie_chart_view.chart()
        chart.removeAllSeries()
        
        # Cria uma nova série
        series = QPieSeries()
        
        # Adiciona os dados à série
        total = sum(status_data.values())
        for status, quantidade in status_data.items():
            percentual = (quantidade / total) * 100
            slice = series.append(f"{status} ({percentual:.1f}%)", quantidade)
            
            # Define cores diferentes para cada status
            if status == "D7+":
                slice.setBrush(QColor(255, 0, 0)) # Vermelho para D7+
            elif status.startswith("D5") or status.startswith("D6"):
                slice.setBrush(QColor(255, 165, 0)) # Laranja para D5-D6
            elif status.startswith("D3") or status.startswith("D4"):
                slice.setBrush(QColor(255, 255, 0)) # Amarelo para D3-D4
            else:
                slice.setBrush(QColor(0, 128, 0)) # Verde para D0-D2
        
        # Adiciona a série ao gráfico
        chart.addSeries(series)
    
    def _atualizar_grafico_barras(self, area_data):
        """
        Atualiza o gráfico de barras com os dados de área.
        
        Args:
            area_data (dict): Dicionário com os dados de área.
        """
        # Obtém o gráfico e remove a série atual
        chart = self.bar_chart_view.chart()
        chart.removeAllSeries()
        
        # Cria uma nova série
        series = QBarSeries()
        
        # Cria um conjunto de barras para cada status
        barset = QBarSet("Quantidade")
        
        # Adiciona os dados ao conjunto de barras
        areas = list(area_data.keys())
        valores = list(area_data.values())
        for valor in valores:
            barset.append(valor)
        
        # Adiciona o conjunto de barras à série
        series.append(barset)
        
        # Adiciona a série ao gráfico
        chart.addSeries(series)
        
        # Atualiza os eixos
        axisX = QBarCategoryAxis()
        axisX.append(areas)
        chart.addAxis(axisX, Qt.AlignBottom)
        series.attachAxis(axisX)
        
        axisY = QValueAxis()
        max_valor = max(valores) if valores else 10
        axisY.setRange(0, max_valor * 1.1) # 10% a mais para margem
        chart.addAxis(axisY, Qt.AlignLeft)
        series.attachAxis(axisY)
    
    def _atualizar_tabela_status(self, status_data):
        """
        Atualiza a tabela de resumo por status.
        
        Args:
            status_data (dict): Dicionário com os dados de status.
        """
        # Limpa a tabela
        self.tabela_status.setRowCount(0)
        
        # Calcula o total
        total = sum(status_data.values())
        
        # Adiciona os dados à tabela
        for i, (status, quantidade) in enumerate(status_data.items()):
            self.tabela_status.insertRow(i)
            
            # Status
            item_status = QTableWidgetItem(status)
            self.tabela_status.setItem(i, 0, item_status)
            
            # Quantidade
            item_quantidade = QTableWidgetItem(str(quantidade))
            item_quantidade.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.tabela_status.setItem(i, 1, item_quantidade)
            
            # Percentual
            percentual = (quantidade / total) * 100 if total > 0 else 0
            item_percentual = QTableWidgetItem(f"{percentual:.1f}%")
            item_percentual.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.tabela_status.setItem(i, 2, item_percentual)
            
            # Define cores diferentes para cada status
            cor = QColor(255, 255, 255) # Branco por padrão
            if status == "D7+":
                cor = QColor(255, 200, 200) # Vermelho claro para D7+
            elif status.startswith("D5") or status.startswith("D6"):
                cor = QColor(255, 230, 200) # Laranja claro para D5-D6
            elif status.startswith("D3") or status.startswith("D4"):
                cor = QColor(255, 255, 200) # Amarelo claro para D3-D4
            else:
                cor = QColor(200, 255, 200) # Verde claro para D0-D2
            
            for j in range(3):
                self.tabela_status.item(i, j).setBackground(QBrush(cor))
        
        # Adiciona uma linha de total
        row = self.tabela_status.rowCount()
        self.tabela_status.insertRow(row)
        
        # Total
        item_total = QTableWidgetItem("Total")
        item_total.setFont(QFont("Arial", 10, QFont.Bold))
        self.tabela_status.setItem(row, 0, item_total)
        
        # Quantidade total
        item_quantidade_total = QTableWidgetItem(str(total))
        item_quantidade_total.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        item_quantidade_total.setFont(QFont("Arial", 10, QFont.Bold))
        self.tabela_status.setItem(row, 1, item_quantidade_total)
        
        # Percentual total (100%)
        item_percentual_total = QTableWidgetItem("100.0%")
        item_percentual_total.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        item_percentual_total.setFont(QFont("Arial", 10, QFont.Bold))
        self.tabela_status.setItem(row, 2, item_percentual_total)
    
    def _atualizar_tabela_area(self, area_data):
        """
        Atualiza a tabela de resumo por área.
        
        Args:
            area_data (dict): Dicionário com os dados de área.
        """
        # Limpa a tabela
        self.tabela_area.setRowCount(0)
        
        # Calcula o total
        total = sum(area_data.values())
        
        # Adiciona os dados à tabela
        for i, (area, quantidade) in enumerate(area_data.items()):
            self.tabela_area.insertRow(i)
            
            # Área
            item_area = QTableWidgetItem(area)
            self.tabela_area.setItem(i, 0, item_area)
            
            # Quantidade
            item_quantidade = QTableWidgetItem(str(quantidade))
            item_quantidade.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.tabela_area.setItem(i, 1, item_quantidade)
            
            # Percentual
            percentual = (quantidade / total) * 100 if total > 0 else 0
            item_percentual = QTableWidgetItem(f"{percentual:.1f}%")
            item_percentual.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.tabela_area.setItem(i, 2, item_percentual)
            
            # Tempo médio (dias) - valor aleatório para exemplo
            tempo_medio = round(random.uniform(2.5, 5.0), 1)
            item_tempo = QTableWidgetItem(f"{tempo_medio}")
            item_tempo.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.tabela_area.setItem(i, 3, item_tempo)
        
        # Adiciona uma linha de total
        row = self.tabela_area.rowCount()
        self.tabela_area.insertRow(row)
        
        # Total
        item_total = QTableWidgetItem("Total")
        item_total.setFont(QFont("Arial", 10, QFont.Bold))
        self.tabela_area.setItem(row, 0, item_total)
        
        # Quantidade total
        item_quantidade_total = QTableWidgetItem(str(total))
        item_quantidade_total.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        item_quantidade_total.setFont(QFont("Arial", 10, QFont.Bold))
        self.tabela_area.setItem(row, 1, item_quantidade_total)
        
        # Percentual total (100%)
        item_percentual_total = QTableWidgetItem("100.0%")
        item_percentual_total.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        item_percentual_total.setFont(QFont("Arial", 10, QFont.Bold))
        self.tabela_area.setItem(row, 2, item_percentual_total)
        
        # Tempo médio total
        tempo_medio_total = round(sum([round(random.uniform(2.5, 5.0), 1) for _ in area_data]) / len(area_data), 1) if area_data else 0
        item_tempo_total = QTableWidgetItem(f"{tempo_medio_total}")
        item_tempo_total.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        item_tempo_total.setFont(QFont("Arial", 10, QFont.Bold))
        self.tabela_area.setItem(row, 3, item_tempo_total)
    
    def _atualizar_tabela_produtividade(self, produtividade_data):
        """
        Atualiza a tabela de produtividade.
        
        Args:
            produtividade_data (list): Lista de dicionários com os dados de produtividade.
        """
        # Limpa a tabela
        self.tabela_produtividade.setRowCount(0)
        
        # Adiciona os dados à tabela
        for i, dados in enumerate(produtividade_data):
            self.tabela_produtividade.insertRow(i)
            
            # Usuário
            item_usuario = QTableWidgetItem(dados["usuario"])
            self.tabela_produtividade.setItem(i, 0, item_usuario)
            
            # Atividades concluídas
            item_concluidas = QTableWidgetItem(str(dados["concluidas"]))
            item_concluidas.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.tabela_produtividade.setItem(i, 1, item_concluidas)
            
            # Tempo médio (dias)
            item_tempo = QTableWidgetItem(f"{dados['tempo_medio']}")
            item_tempo.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.tabela_produtividade.setItem(i, 2, item_tempo)
            
            # Atividades em andamento
            item_andamento = QTableWidgetItem(str(dados["em_andamento"]))
            item_andamento.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.tabela_produtividade.setItem(i, 3, item_andamento)
            
            # Eficiência
            eficiencia = dados["eficiencia"] * 100
            item_eficiencia = QTableWidgetItem(f"{eficiencia:.1f}%")
            item_eficiencia.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.tabela_produtividade.setItem(i, 4, item_eficiencia)
            
            # Define cores com base na eficiência
            cor = QColor(255, 255, 255) # Branco por padrão
            if eficiencia >= 90:
                cor = QColor(200, 255, 200) # Verde claro para alta eficiência
            elif eficiencia >= 80:
                cor = QColor(255, 255, 200) # Amarelo claro para média eficiência
            else:
                cor = QColor(255, 200, 200) # Vermelho claro para baixa eficiência
            
            self.tabela_produtividade.item(i, 4).setBackground(QBrush(cor))
        
        # Adiciona uma linha de média
        row = self.tabela_produtividade.rowCount()
        self.tabela_produtividade.insertRow(row)
        
        # Média
        item_media = QTableWidgetItem("Média")
        item_media.setFont(QFont("Arial", 10, QFont.Bold))
        self.tabela_produtividade.setItem(row, 0, item_media)
        
        # Média de atividades concluídas
        media_concluidas = sum(dados["concluidas"] for dados in produtividade_data) / len(produtividade_data) if produtividade_data else 0
        item_media_concluidas = QTableWidgetItem(f"{media_concluidas:.1f}")
        item_media_concluidas.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        item_media_concluidas.setFont(QFont("Arial", 10, QFont.Bold))
        self.tabela_produtividade.setItem(row, 1, item_media_concluidas)
        
        # Média de tempo médio
        media_tempo = sum(dados["tempo_medio"] for dados in produtividade_data) / len(produtividade_data) if produtividade_data else 0
        item_media_tempo = QTableWidgetItem(f"{media_tempo:.1f}")
        item_media_tempo.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        item_media_tempo.setFont(QFont("Arial", 10, QFont.Bold))
        self.tabela_produtividade.setItem(row, 2, item_media_tempo)
        
        # Média de atividades em andamento
        media_andamento = sum(dados["em_andamento"] for dados in produtividade_data) / len(produtividade_data) if produtividade_data else 0
        item_media_andamento = QTableWidgetItem(f"{media_andamento:.1f}")
        item_media_andamento.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        item_media_andamento.setFont(QFont("Arial", 10, QFont.Bold))
        self.tabela_produtividade.setItem(row, 3, item_media_andamento)
        
        # Média de eficiência
        media_eficiencia = sum(dados["eficiencia"] for dados in produtividade_data) / len(produtividade_data) * 100 if produtividade_data else 0
        item_media_eficiencia = QTableWidgetItem(f"{media_eficiencia:.1f}%")
        item_media_eficiencia.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        item_media_eficiencia.setFont(QFont("Arial", 10, QFont.Bold))
        self.tabela_produtividade.setItem(row, 4, item_media_eficiencia)

# Instruções para integração
"""
Para integrar a aba de gestão à interface principal, siga estas etapas:

1. Adicione as importações necessárias no início do arquivo main_window.py:
   
   from PyQt5.QtChart import QChart, QChartView, QPieSeries, QBarSeries, QBarSet, QBarCategoryAxis, QValueAxis
   
   Nota: Você precisará instalar o pacote PyQtChart:
   pip install PyQtChart

2. Copie a classe GestaoView para um novo arquivo chamado gestao_view.py no diretório app/ui/

3. No método _init_ui da classe MainWindow, adicione uma nova tab para a visão de gestão:
   
   # Tab de gestão
   from app.ui.gestao_view import GestaoView
   self.tab_gestao = GestaoView()
   self.tabs.addTab(self.tab_gestao, "Gestão")

4. Certifique-se de que os dados necessários estão sendo passados para a aba de gestão.
   Em uma implementação real, você precisará modificar os métodos da classe GestaoView
   para obter dados reais do banco de dados em vez de usar dados de exemplo.
"""
"""
Módulo para implementação da aba de gestão com visão gerencial.
Este código deve ser integrado à classe MainWindow no arquivo main_window.py.
"""
