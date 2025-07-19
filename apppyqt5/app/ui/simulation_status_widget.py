# """
# Widget para exibir o status de simulação do banco de dados.
# """
# from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel
# from PyQt5.QtGui import QColor, QPalette
# from PyQt5.QtCore import Qt

# class SimulationStatusWidget(QWidget):
#     """
#     Widget que exibe o status de simulação do banco de dados.
#     """
    
#     def __init__(self, parent=None):
#         """
#         Inicializa o widget de status de simulação.
        
#         Args:
#             parent (QWidget, optional): Widget pai.
#         """
#         super().__init__(parent)
        
#         # Inicializa a interface
#         self._init_ui()
        
#         # Estado inicial
#         self.set_simulation_status(False, False, False)
    
#     def _init_ui(self):
#         """Inicializa a interface do usuário."""
#         layout = QHBoxLayout(self)
#         layout.setContentsMargins(5, 2, 5, 2)
        
#         # Label para o status
#         self.lbl_status = QLabel("Banco de Dados: Real")
#         self.lbl_status.setAlignment(Qt.AlignCenter)
#         layout.addWidget(self.lbl_status)
        
#         # Configura o estilo
#         self.setAutoFillBackground(True)
#         self._set_background_color(QColor(200, 255, 200))  # Verde claro
    
#     def _set_background_color(self, color):
#         """
#         Define a cor de fundo do widget.
        
#         Args:
#             color (QColor): Cor de fundo.
#         """
#         palette = self.palette()
#         palette.setColor(QPalette.Window, color)
#         self.setPalette(palette)
    
#     def set_simulation_status(self, oracle_simulated, hana_simulated, forced):
#         """
#         Define o status de simulação.
        
#         Args:
#             oracle_simulated (bool): Se o Oracle está em modo simulado.
#             hana_simulated (bool): Se o HANA está em modo simulado.
#             forced (bool): Se o modo simulado foi forçado.
#         """
#         # Determina o texto e a cor com base no status
#         if oracle_simulated and hana_simulated:
#             if forced:
#                 text = "Banco de Dados: SIMULADO (Forçado)"
#                 color = QColor(255, 200, 200)  # Vermelho claro
#             else:
#                 text = "Banco de Dados: SIMULADO"
#                 color = QColor(255, 230, 200)  # Laranja claro
#         elif oracle_simulated:
#             text = "Oracle: SIMULADO, HANA: Real"
#             color = QColor(255, 255, 200)  # Amarelo claro
#         elif hana_simulated:
#             text = "Oracle: Real, HANA: SIMULADO"
#             color = QColor(255, 255, 200)  # Amarelo claro
#         else:
#             text = "Banco de Dados: Real"
#             color = QColor(200, 255, 200)  # Verde claro
        
#         # Atualiza a interface
#         self.lbl_status.setText(text)
#         self._set_background_color(color)
