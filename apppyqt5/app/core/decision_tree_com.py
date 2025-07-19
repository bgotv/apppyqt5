"""
Módulo de árvore de decisão para análise técnica.
Implementa a árvore de perguntas conforme o código original.
"""
import os
from PyQt5.QtCore import Qt, pyqtSignal, QObject
import time
import webbrowser
import traceback
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, 
    QCheckBox, QMessageBox, QApplication
)
from PyQt5.QtCore import Qt, pyqtSignal

from app.utils.logger import log_action
from app.utils.performance import measure_performance
from app.config import settings
from app.database.hana_connector import consultar_uc_hana
import time
import datetime

class SafeDict(dict):
    """
    Dicionário seguro para formatação de strings.
    Retorna uma string vazia para chaves não encontradas.
    """
    def __missing__(self, key):
        return '{' + key + '}'

class CheckboxDialog(QDialog):
    """
    Diálogo com checkboxes para seleção múltipla.
    """
    def __init__(self, parent, title, options):
        super().__init__(parent)
        self.setWindowTitle("Seleção Múltipla")
        self.setMinimumWidth(400)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        
        self.selected_options = []
        
        layout = QVBoxLayout(self)
        
        # Título
        title_label = QLabel(title)
        title_label.setWordWrap(True)
        layout.addWidget(title_label)
        
        # Checkboxes
        self.checkboxes = []
        for option in options:
            checkbox = QCheckBox(option)
            self.checkboxes.append(checkbox)
            layout.addWidget(checkbox)
        
        # Botões
        button_layout = QHBoxLayout()
        
        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.accept)
        button_layout.addWidget(self.ok_button)
        
        layout.addLayout(button_layout)
    
    def accept(self):
        """Aceita o diálogo e armazena as opções selecionadas."""
        self.selected_options = [cb.text() for cb in self.checkboxes if cb.isChecked()]
        super().accept()

class OptionDialog(QDialog):
    """
    Diálogo com opções para seleção única.
    """
    def __init__(self, parent, question, options, copy_text=None):
        super().__init__(parent)
        self.setWindowTitle("Pergunta")
        self.setMinimumWidth(400)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        
        self.answer = None
        
        layout = QVBoxLayout(self)
        
        # Pergunta
        question_label = QLabel(question)
        question_label.setWordWrap(True)
        layout.addWidget(question_label)
        
        # Botões de opção
        for option in options:
            button = QPushButton(option)
            button.clicked.connect(lambda checked, opt=option: self._on_option_clicked(opt))
            layout.addWidget(button)
    
    def _on_option_clicked(self, option):
        """
        Handler para clique em uma opção.
        
        Args:
            option (str): Opção selecionada.
        """
        self.answer = option
        self.accept()

class DecisionTree(QObject):
    def set_context(self, note_id, user_id):
        self.note_id = note_id
        self.user_id = user_id
    """
    Implementa a árvore de decisão para análise técnica de notas.
    """
        # Sinais que o DecisionTree vai expor
    question_answered  = pyqtSignal(str, str)   # (question_id, answer)
    analysis_completed = pyqtSignal()
    
    def __init__(self, flags_manager=None, parent=None):
        """
        Inicializa a árvore de decisão.
        
        Args:
            flags_manager (FlagsManager, optional): Gerenciador de flags.
            parent (QWidget, optional): Widget pai para os diálogos.
        """
        # Não chame super().__init__() aqui, pois a classe não herda de nada
        super().__init__(parent)
        self.flags_manager = flags_manager
        self.parent = parent
        self.history = {}  # Histórico de respostas
        self.pendencias = []  # Lista de pendências
        self.data = {}  # Dados da nota e UC
        
        # Sinais
        self.question_answered = None
        self.analysis_completed = None
        
        # Inicializa a árvore de perguntas
        self._init_tree()

    def has_pendencias(self):
        # Verifica se há pendências na lista tradicional
        if self.pendencias:
            return True
        
        # Verifica se há flags ativas que causam indeferimento
        for flag_id, value in self.flags.items():
            if value:
                flag_info = self.flags_manager.get_flag_info(flag_id)
                if flag_info and flag_info.get('indeferimento', True):
                    return True
        
        return False

    
    def _init_tree(self):
        """Inicializa a estrutura da árvore de perguntas."""
        # Fluxo atualizado com flags. Cada nó pode definir:
        # - "flag_if_no": valor da flag a ser acionado se resposta for "não"
        # - "flag_if": dicionário com respostas e os flags a serem definidos
        # - "flag_if_no_condition": condição para flag se resposta for "não"
        # - "flag_if_sim_condition": condição para flag se resposta for "sim"
        self.tree = {
             "tela_aviso": {
                "question": "Por gentileza, entre no box da região {BOX_PROJETO} no site PP, selecione o limite de exibições para 1000 e pesquise a atividade para movê-la para o seu inbox. Pressione OK para continuar.",
                "options": ["OK"],
                "responses": {
                    "ok": "tipo_documento"
                }
            },
            "tipo_documento": {
                "question": "PF ou PJ? (Tipo: {variavel_pf_pj')",
                "options": ["PF", "PJ"],
                "responses": {
                    "pf": "anexoE_disponivel",
                    "pj": "anexoE_disponivel"
                }
            },
            "anexoE_disponivel": {
                "question": "O ANEXO E está disponível?",
                "options": ["Sim", "Não"],
                "responses": {
                    "sim": "anexoE_legivel",
                    "não": {
                        "pf": "documentacao_pf",
                        "pj": "documentacao_pj"
                    }
                },
                "flag_if_no": "flag_anexoe"
            },
            "anexoE_legivel": {
                "question": "O ANEXO E está legível?",
                "options": ["Sim", "Não"],
                "responses": {
                    "sim": "anexoE_atualizado",
                    "não": "anexoE_atualizado"
                },
                "flag_if_no": 25
            },
            "anexoE_atualizado": {
                "question": "O ANEXO E está atualizado?",
                "options": ["Sim", "Não"],
                "responses": {
                    "sim": "documental",
                    "não": "documental"
                },
                "flag_if_no": 26
            },
            "documental": {
                "question": "A instalação do site PP ({CD_UC}) confere com o SAP ({COD_INSTALACAO}) e com o anexo E?",
                "options": ["Sim", "Não"],
                "responses": {
                    "sim": "tipo_geracao",
                    "não": "tipo_geracao"
                },
                "flag_if_no": 1,
                "flag_if_status": { "field": "STATUS_INSTALACAO", "not": "Não Suspensa", "flag": 2 }
            },
            "tipo_geracao": {
                "question": "O tipo de geração indicado no site ({CCSP_FONTEGER}) é igual ao do anexo E?",
                "options": ["Sim", "Não"],
                "responses": {
                    "sim": "modalidade_compensacao",
                    "não": "modalidade_compensacao"
                },
                "flag_if_no": 3
            },
            "modalidade_compensacao": {
                "question": "A modalidade indicada no site ({MOD_PP}) é similar à do anexo E?",
                "options": ["Sim", "Não"],
                "responses": {
                    "sim": "potencia",
                    "não": "potencia"
                },
                "flag_if_no_condition": { "field": "MOD_PP", "local": 23, "remoto": 24 }
            },
            "potencia": {
                "question": "A potência indicada no site ({CCSP_POTMICROGER}) é similar à indicada no anexo E?",
                "options": ["Sim", "Não"],
                "responses": {
                    "sim": "fast_track",
                    "não": "fast_track_supera"
                },
            },
            "fast_track_supera": {
                "question": "Aviso: O cliente selecionou opções incompatíveis com o Fast Track. O cliente selecionou algum item do Fast Track?",
                "options": ["Sim", "Não"],
                "responses": {
                    "sim": "art_91_comum",
                    "não": "art_91_comum"
                },
            },
            "fast_track": {
                "question": "O cliente indicou potência e modalidade de consumo compatíveis com Fast Track. A opção de Fast Track foi selecionada no anexo?",
                "options": ["Sim", "Não"],
                "responses": {
                    "sim": "art_91_fast_track",
                    "não": "art_91_comum"
                },

            },
            "art_91_fast_track": {
                "question": "O item 'Art. 68 ou 91' foi selecionado?",
                "options": ["Sim", "Não"],
                "responses": {
                    "sim": "itens_obrigatorios_fast_track",
                    "não": "itens_obrigatorios_fast_track"
                },

            },
            "itens_obrigatorios_fast_track": {
                "question": "Os itens obrigatórios (4.4 e 4.6) foram marcados?",
                "options": ["Sim", "Não"],
                "responses": {
                    "sim": "item_6_fast",
                    "não": "item_6_fast"
                },
                "flag_if_no": 4
            },
            "item_6_fast": {
                "question": "O Item 6 (fast track) foi devidamente assinado digitalmente ou com assinatura manuscrita original (Não devem ser aceitas assinaturas coladas ou inseridas como imagem no documento)",
                "options": ["Sim", "Não"],
                "responses": {
                    "sim": "documentacao",
                    "não": "documentacao"
                },
                "flag_if_no": 5
            },
            "art_91_comum": {
                "question": "O item 'Art. 68 ou 91' foi selecionado?",
                "options": ["Sim", "Não"],
                "responses": {
                    "sim": "itens_obrigatorios_comum",
                    "não": "itens_obrigatorios_comum"
                },
                    "flag_if_yes": "flag_91_sim",
                    "flag_if_no": "flag_91_nao"
            },
            "itens_obrigatorios_comum": {
                "question": "Os itens obrigatórios (4.4 e 4.6) foram marcados?",
                "options": ["Sim", "Não"],
                "responses": {
                    "sim": "documentacao",
                    "não": "documentacao"
                },
                "flag_if_no": 6
            },
            "documentacao": {
                "question": "Conferir documentação. Se PF, segue para documentacao_pf; se PJ, segue para documentacao_pj.",
                "options": ["PF", "PJ"],
                "responses": {
                    "pf": "enviou_doc_pf",
                    "pj": "documentacao_pj"
                }
            },
            "enviou_doc_pf": {
                "question": "As documentações pessoais do cliente foram enviadas?",
                "options": ["Sim", "Não"],
                "responses": {
                    "sim": "documentacao_pf",
                    "não": "documentacao_pf"
                },
                "flag_if_no": "flag_doc_pf"
            },
            "documentacao_pf": {
                "question": "O CPF e o Nome do titular da UC são {NUMERO_DOC}, {NOME_RAZAO}?",
                "options": ["Sim", "Não"],
                "responses": {
                    "sim": "procuracao_pf",
                    "não": "procuracao_pf"
                },
                "flag_if_no": "flag_cpf"
            },
            "procuracao_pf": {
                "question": "Foi indicado procurador no ANEXO E?",
                "options": ["Sim", "Não"],
                "responses": {
                    "sim": "procuraçao_ok",
                    "não": "assinaturas_anexo"
                }
            },
            "procuraçao_ok": {
                "question": "A procuração foi enviada?",
                "options": ["Sim", "Não"],
                "responses": {
                    "sim": "assinaturas_anexo_procura",
                    "não": "finaliza"
                    # "não": "finaliza_comercial"
                },
                "flag_if_no": 15
            },
            "assinaturas_anexo_procura": {
                "question": "A procuração está conforme junto com as assinaturas no anexo E e nos documentos pessoais?",
                "options": ["Sim", "Não"],
                "responses": {
                    "sim": "finaliza",
                    "não": "finaliza"
                    # "sim": "finaliza_comercial",
                    # "não": "finaliza_comercial"
                },
                "flag_if_no": 13
            },
            "assinaturas_anexo": {
                "question": "As assinaturas nos documentos (pessoal e anexo E) estão conforme?",
                "options": ["Sim", "Não"],
                "responses": {
                    "sim": "finaliza",
                    "não": "finaliza"
                    # "sim": "finaliza_comercial",
                    # "não": "finaliza_comercial"
                },
                "flag_if_no": 14,
                # "flag_if_yes": {"flag_aprovado": "SIM"}
            },
            "documentacao_pj": {
                "question": "Selecione o tipo de cliente PJ",
                "options": ["ME/MEI", "LTDA/SA", "PRODUTOR RURAL", "ASSOCIAÇÕES"],
                "responses": {
                    "me/mei": "confere_documento",
                    "ltda/sa": "confere_contrato",
                    "produtor rural": "confere_isencao",
                    "associações": "confere_ata"                    
                }
            },
            "confere_documento": {
                "question": "Marque se houver alguma inconsistência abaixo:",
		"dialog_type": "checkbox",
                "options": ["Cartão CNPJ não enviado", "Representante não enviou documentos", "Nome do representante não consta nos documentos enviados", "Assinaturas não conferem entre si", "Não foram constatadas divergências"],
                "responses": {
                    # "default": "finaliza_comercial",
                    # "Não foram constatadas divergências": "finaliza_comercial",
                    # "Cartão CNPJ não enviado": "finaliza_comercial",
                    # "Representante não enviou documentos": "finaliza_comercial",
                    # "Nome do representante não consta nos documentos enviados": "finaliza_comercial",
                    # "Assinaturas não conferem entre si": "finaliza_comercial"
                    "default": "finaliza",
                    "Não foram constatadas divergências": "finaliza",
                    "Cartão CNPJ não enviado": "finaliza",
                    "Representante não enviou documentos": "finaliza",
                    "Nome do representante não consta nos documentos enviados": "finaliza",
                    "Assinaturas não conferem entre si": "finaliza"
                },
                "flag_if_Cartão CNPJ não enviado": 21,
                "flag_if_Representante não enviou documentos": 17,
                "flag_if_Nome do representante não consta nos documentos enviados": 18,
                "flag_if_Assinaturas não conferem entre si": 19
            },
            "confere_ata": {
                "question": "Enviada a Ata de eleição/assembleia?",
                "options": ["Sim", "Não"],
                "responses": {
                    "sim": "documento_representante",
                    "não": "documento_representante"
                },
                "flag_if_no": 20,
                # "flag_if_yes": {"flag_aprovado": "SIM"}
            },
            "documento_representante": {
                "question": "O documento do representante confere com anexos?",
                "options": ["Sim", "Não"],
                "responses": {
                    "sim": "finaliza",
                    "não": "finaliza"
                    # "sim": "finaliza_comercial",
                    # "não": "finaliza_comercial"
                },
                "flag_if_no": 20,
                # "flag_if_yes": {"flag_aprovado": "SIM"}
            },
            "confere_isencao": {
                "question": "O produtor rural tem isenção de ICMS?",
                "options": ["Sim", "Não"],
                "responses": {
                    "sim": "confere_cadesp",
                    "não": "confere_documento"
                },
                "flag_if_no": 14,
                # "flag_if_yes": {"flag_aprovado": "SIM"}
            },
            "confere_cadesp": {
                "question": "O cliente enviou a inscrição completa (3 páginas) para produtor rural?",
                "options": ["Sim", "Não"],
                "responses": {
                    "sim": "confere_documento",
                    "não": "confere_documento"
                },
                "flag_if_no": 22,
                # "flag_if_yes": {"flag_aprovado": "SIM"}
            },
            "confere_contrato": {
                "question": "Enviado o Contrato/Estatuto Social?",
                "options": ["Sim", "Não"],
                "responses": {
                    "sim": "confere_documento",
                    "não": "confere_documento"
                },
                "flag_if_no": 22,
                # "flag_if_yes": {"flag_aprovado": "SIM"}
            },
            "finaliza_comercial": {
                "question": "Processo comercial finalizado. Clique OK para ver o resumo.",
                "options": ["OK"],
                "responses": {
                    "ok": "sist_geracao"
                }
            },
            "sist_geracao": {
                "question": "O sistema de geração é o mesmo que {CCSP_FONTEGER}?",
                "options": ["Sim", "Não"],
                "responses": {
                    "sim": "anexoE_tec",
                    "não": "anexoE_tec"
                },
                "flag_if_no": 140
            },
            "anexoE_tec": {
                "action": "open_folder",
                "message": "Abra o anexo E e clique OK para abrir a pasta da nota.",
                "next": "item_4_5_3_tec"
            },
            "item_4_5_3_tec": {
                "question": "O item 4.5.3 foi assinalado?",
                "options": ["Sim", "Não"],
                "responses": {
                    "sim": "verifica_fast_tec",
                    "não": "nome_cpf_cliente"
                }
            },
            "verifica_fast_tec": {
                "action": "check_fast",
                "next": "nome_cpf_cliente",
                "flag_if_condition": {
                    "condition": "cd_cliente_gt",  # se cd_cliente > 7.5
                    "flag": 33
                }
            },
            "nome_cpf_cliente": {
                "question": "O CPF e o Nome do titular da UC são {NUMERO_DOC}, {NOME_RAZAO}",
                "options": ["Sim", "Não"],
                "responses": {
                    "sim": "endereco_cliente",
                    "não": "endereco_cliente"
                },
                "flag_if_no": 108
            },
            "endereco_cliente": {
                "question": "O endereço da instalação é o mesmo de {RUA_CCS} {NUM_RUA_CCS}?",
                "options": ["Sim", "Não"],
                "responses": {
                    "sim": "numero_fases",
                    "não": "numero_fases"
                },
                "flag_if_no": 109
            },
            "numero_fases": {
                "question": "O número de fases e a corrente nominal do disjuntor e CCS são os mesmos de {NUM_FASES} e {corrente_nominal_CCS}?",
                "options": ["Sim", "Não"],
                "responses": {
                    "sim": "qtd_modulos",
                    "não": "qtd_modulos"
                },
                "flag_if_no": 111
            },
            "qtd_modulos": {
                "question": "A quantidade de módulos é a mesma de {qnt_mod_site}?",
                "options": ["Sim", "Não"],
                "responses": {
                    "sim": "qtd_inversores",
                    "não": "qtd_inversores"
                },
                "flag_if_no": 112
            },
            "qtd_inversores": {
                "question": "A quantidade de inversores é a mesma de {qnt_inv_site}?",
                "options": ["Sim", "Não"],
                "responses": {
                    "sim": "potencia_total_modulos",
                    "não": "potencia_total_modulos"
                },
                "flag_if_no": 113
            },
            "potencia_total_modulos": {
                "question": "A potência total dos módulos é a mesma do {potencia_total_mod_site}?",
                "options": ["Sim", "Não"],
                "responses": {
                    "sim": "potencia_total_inversores",
                    "não": "potencia_total_inversores"
                },
                "flag_if_no": 116
            },
            "potencia_total_inversores": {
                "question": "A potência total dos módulos e inversores é a mesma do {potencia_total_inv_site}?",
                "options": ["Sim", "Não"],
                "responses": {
                    "sim": "fabricante_modelo_mod",
                    "não": "fabricante_modelo_mod"
                },
                "flag_if_no": 117
            },
            "fabricante_modelo_mod": {
                "question": "O fabricante e o modelo dos módulos são os mesmos de {fabricante_mod_site} e {modelo_mod_site}?",
                "options": ["Sim", "Não"],
                "responses": {
                    "sim": "fabricante_modelo_inv",
                    "não": "fabricante_modelo_inv"
                },
                "flag_if_no": 114
            },
            "fabricante_modelo_inv": {
                "question": "O fabricante e o modelo dos inversores são os mesmos de {fabricante_inv_site} e {modelo_inv_site}?",
                "options": ["Sim", "Não"],
                "responses": {
                    "sim": "menor_potencia",
                    "não": "menor_potencia"
                },
                "flag_if_no": 115
            },
            "menor_potencia": {
                "question": "A menor potência entre os módulos e inversores é essa {menor_potencia_site}?",
                "options": ["Sim", "Não"],
                "responses": {
                    "sim": "certificado_inmetro_tec",
                    "não": "certificado_inmetro_tec"
                },
                "flag_if_no": 122
            },
            "certificado_inmetro_tec": {
                "action": "open_link",
                "message": "Clique no link para abrir o site do Inmetro: https://registro.inmetro.gov.br/consulta",
                "next": "portaria_tec"
            },
            "portaria_tec": {
                "question": "A portaria é 140 ou 150 ou a data de concessão é superior a 01/02/2025 ou existe o teste de conformidade anexado?",
                "options": ["Sim", "Não"],
                "responses": {
                    "sim": "modelo_inversor",
                    "não": "modelo_inversor"
                },
                "flag_if_no": 125
            },
            "modelo_inversor": {
                "question": "Quando o modelo do inversor previsto no projeto é igual ao que consta no registro?",
                "options": ["Sim", "Não"],
                "responses": {
                    "sim": "declaracao_apresentada",
                    "não": "declaracao_apresentada"
                },
                "flag_if_no": 124
            },
            "declaracao_apresentada": {
                "question": "O documento apresentado para comprovar as questões relacionadas à função de AFCI do inversor atende aos critérios?",
                "options": ["Sim", "Não"],
                "responses": {
                    "sim": "campo_profissional_final",
                    "não": "campo_profissional_final"
                },
                "flag_if_no": 126
            },
            "campo_profissional_final": {
                "action": "open_folder",
                "message": "Abra a ART/TRT e clique OK para abrir a pasta da nota.",
                "next": "campo_profissional_final_q"
            },
            "campo_profissional_final_q": {
                "question": "O campo do profissional é o mesmo do {campo_profissional_site}?",
                "options": ["Sim", "Não"],
                "responses": {
                    "sim": "proprietario",
                    "não": "proprietario"
                },
                "flag_if_no": 101
            },
            "proprietario": {
                "question": "O proprietário da instalação é o mesmo do {proprietario_site}?",
                "options": ["Sim", "Não"],
                "responses": {
                    "sim": "endereco_art",
                    "não": "endereco_art"
                },
                "flag_if_no": 102
            },
            "endereco_art": {
                "question": "O endereço ART/TRT é o mesmo que {endereco_art_site}?",
                "options": ["Sim", "Não"],
                "responses": {
                    "sim": "campo_atividade_art",
                    "não": "campo_atividade_art"
                },
                "flag_if_no": 103
            },
            "campo_atividade_art": {
                "question": "O campo de atividade técnica possui indicação de projeto?",
                "options": ["Sim", "Não"],
                "responses": {
                    "sim": "art_trt_definitiva",
                    "não": "art_trt_definitiva"
                },
                "flag_if_no": 104
            },
            "art_trt_definitiva": {
                "question": "Há documento de responsabilidade técnica registrado e devidamente pago?",
                "options": ["Sim", "Não"],
                "responses": {
                    "sim": "assinatura_art_trt",
                    "não": "assinatura_art_trt"
                },
                "flag_if_no": 105
            },
            "assinatura_art_trt": {
                "question": "O documento de responsabilidade técnica está devidamente assinado?",
                "options": ["Sim", "Não"],
                "responses": {
                    "sim": "finaliza",
                    "não": "finaliza"
                },
                "flag_if_no": 106
            },
            "finaliza": {
                "question": "Processo finalizado. Clique OK para ver o resumo.",
                "options": ["OK"],
                "responses": {
                    "ok": None
                }
            }
        }
        
        # Inicializa todas as flags (0 ou valor padrão)
        self.flags = {
            "flag_anexoe": 0,
            25: 0,
            26: 0,
            1: 0,
            2: 0,
            3: 0,
            23: 0,
            24: 0,
            28: 0,
            29: 0,
            "flag_reprova_remoto": 0,
            4: 0,
            5: 0,
            6: 0,
            "flag_cpf": 0,
            "flag_doc_pf": 0,
            15: 0,
            13: 0,
            14: 0,
            27: 0,
            108: 0,
            109: 0,
            111: 0,
            112: 0,
            113: 0,
            116: 0,
            117: 0,
            114: 0,
            115: 0,
            122: 0,
            123: 0,
            125: 0,
            124: 0,
            126: 0,
            101: 0,
            102: 0,
            103: 0,
            104: 0,
            105: 0,
            106: 0
        }
    
    def clear_history(self):
        """Limpa o histórico de respostas e pendências."""
        self.history = {}
        self.pendencias = []
        
        # Reinicia todas as flags
        for key in self.flags:
            self.flags[key] = 0
        
        log_action('decision_tree_history_cleared')
    
    def set_data(self, note_data=None, uc_data=None):
        """
        Define os dados da nota e UC para uso na árvore.
        
        Args:
            note_data (dict, optional): Dados da nota técnica.
            uc_data (dict, optional): Dados da unidade consumidora.
        """
        self.data = {}
        
        # Adiciona dados da nota
        if note_data:
            self.data.update(note_data)
        
        # Adiciona dados da UC
        if uc_data:
            self.data.update(uc_data)
        
        log_action('decision_tree_data_set', {
            'note_data_keys': list(note_data.keys()) if note_data else None,
            'uc_data_keys': list(uc_data.keys()) if uc_data else None
        })
    
    @measure_performance
    def run_tree(self, start_key="tela_aviso"):
        """
        Executa a árvore de perguntas a partir de um nó específico.
        
        Args:
            start_key (str, optional): Chave do nó inicial.
            
        Returns:
            tuple: Tupla com histórico de respostas e lista de pendências.
        """
        num_contrato = str(self.data.get("NUM_CONTRATO", "") or "").strip()
        if not num_contrato:
            QMessageBox.warning(
                self.parent,
                "Contrato Não Encontrado",
                "Não foi encontrado contrato ativo no sistema.\n"
                "A análise será automaticamente INDEFERIDA."
            )
            # ativa a flag 200
            self.flags[29] = 1
            # registra pendência
            if self.flags_manager:
                self.flags_manager.set_flag(29, 1)
                # só adiciona em pendencias se indeferimento
                flag_info = self.flags_manager.get_flag_info(29)
                if flag_info and flag_info.get('indeferimento', True):
                    self.pendencias.append(29)
            # dispara sinal de conclusão para a UI (opcional)
            if self.analysis_completed:
                self.analysis_completed.emit()
            # **retorna antes de entrar no while**, interrompendo toda a árvore
            return self.history, self.pendencias
        
        current = start_key
        
        while current is not None:
            try:
                # Verifica se a chave existe na árvore
                if current not in self.tree:
                    log_action('decision_tree_key_error', {'key': current})
                    QMessageBox.critical(
                        self.parent,
                        "Erro na Árvore de Decisão",
                        f"Chave '{current}' não encontrada na árvore de decisão.\n\nA análise será interrompida."
                    )
                    break
                
                node = self.tree[current]
                t0 = time.time()
                
                # Tratamento automático para nó "tipo_documento"
                if current == "tipo_documento" and self.data:
                    tipo = self.data.get("TIPO_DOCUMENTO", "").upper()
                    if not tipo:
                        tipo = "PF"  # Valor padrão
                    self.history[current] = tipo
                    log_action('tipo_documento_auto', {'tipo': tipo})
                    next_key = node["responses"].get(tipo.lower())
                    current = next_key
                    continue
                
                # Tratamento automático para nó "documentacao" (se necessário)
                if current == "documentacao" and self.data:
                    tipo = self.data.get("TIPO_DOCUMENTO", "").upper()
                    if not tipo:
                        tipo = "PJ"
                    self.history[current] = tipo
                    log_action('documentacao_auto', {'tipo': tipo})
                    next_key = node["responses"].get(tipo.lower())
                    current = next_key
                    continue
                
                # Se o nó tiver uma ação, executa-a
                if "action" in node:
                    act = node["action"]
                    msg = node.get("message", "Ação necessária.")
                    
                    if act == "open_folder":
                        QMessageBox.information(self.parent, "Ação", msg)
                        if self.data.get("downloads_folder"):
                            os.startfile(self.data.get("downloads_folder"))
                    
                    elif act == "open_link":
                        QMessageBox.information(self.parent, "Ação", msg)
                        webbrowser.open(settings.INMETRO_SITE_URL)
                    
                    elif act == "check_fast" and self.data:
                        try:
                            cd_cliente = float(self.data.get("vl_potencia_gerador", 999))
                        except:
                            cd_cliente = 999
                        
                        if cd_cliente < 7.5:
                            self.history["fast"] = "sim"
                            log_action('fast_track_check', {
                                'item_4_5_3': 'sim',
                                'potencia': cd_cliente,
                                'fast': 'sim'
                            })
                        else:
                            self.history["fast"] = "não"
                            log_action('fast_track_check', {
                                'item_4_5_3': 'sim',
                                'potencia': cd_cliente,
                                'fast': 'não'
                            })
                    
                    current = node.get("next")
                    continue
                
                # Formata o texto da pergunta
                try:
                    question_text = node["question"].format_map(SafeDict(self.data))
                except ValueError as e:
                    log_action('question_format_error', {'error': str(e)})
                    question_text = node["question"]
                    

                
                # Se o nó utiliza checkbox (seleção múltipla), trata-o com CheckboxDialog
                if node.get("dialog_type") == "checkbox":
                    dlg = CheckboxDialog(self.parent, question_text, node["options"])
                    result = dlg.exec_()
                    if result != QDialog.Accepted:
                        break
                    duration = time.time() - t0
                    # pega a lista de opções marcadas e monta a string para o log
                    raw_sel = dlg.selected_options  # lista de strings
                    answer_for_log = ",".join(raw_sel).lower()

                    # log de timing
                    log_action('question_timing', {
                        'note_id': getattr(self, 'note_id', None),
                        'user_id': getattr(self, 'user_id', None),
                        'question_id': current,
                        'answer': answer_for_log,
                        'duration_s': round(duration, 3),
                        'timestamp': datetime.datetime.utcnow().isoformat()
                    })
                                    

                    
                    # selected = dlg.selected_options
                    self.history[current] = raw_sel
                    
                    # Para cada opção selecionada, ativa as flags correspondentes
                    for opt in raw_sel:
                        opt_clean = opt.strip().lower()
                        for key in node:
                            if key.startswith("flag_if_") and key != "flag_if":
                                expected_option = key[len("flag_if_"):].strip().lower()
                                if expected_option in opt_clean:
                                    flag_val = node[key]
                                    if isinstance(flag_val, dict):
                                        for fkey, fvalue in flag_val.items():
                                            self.flags[fkey] = fvalue
                                            log_action('flag_set', {
                                                'node': current,
                                                'option': opt,
                                                'flag': fkey,
                                                'value': fvalue
                                            })
                                    else:
                                        self.flags[flag_val] = 1
                                        log_action('flag_activated', {
                                            'node': current,
                                            'option': opt,
                                            'flag': flag_val
                                        })
                                        
                    self.history[current] = answer_for_log
                    # Define o próximo nó
                    next_key = node["responses"].get("default", "finaliza")
                    current = next_key
                    continue
                
                # Para nós do tipo padrão (OptionDialog)
                copy_text = None
                if current == "tela_aviso" and self.data:
                    copy_text = self.data.get("NR_ATIVIDADE", "")
                
                dlg = OptionDialog(self.parent, question_text, node["options"], copy_text=copy_text)
                result = dlg.exec_()
                if result != QDialog.Accepted or dlg.answer is None:
                    break
                duration = time.time() - t0
                raw_answer = dlg.answer.strip()
                answer_for_log = raw_answer.lower()
                log_action('question_timing', {
                    'note_id': getattr(self, 'note_id', None),
                    'user_id': getattr(self, 'user_id', None),
                    'question_id': current,
                    'answer': answer_for_log,
                    'duration_s': round(duration, 3),
                    'timestamp': datetime.datetime.utcnow().isoformat()
                })
                

                self.history[current] = answer_for_log

                answer = dlg.answer
                answer_clean = answer.strip().lower()
                self.history[current] = answer_clean                

                
                # Emite sinal de resposta
                if hasattr(self, 'question_answered') and self.question_answered is not None:
                    self.question_answered.emit(current, answer_clean)
                
                # Processa flags conforme a lógica atual
                if "flag_if_no" in node and answer_clean == "não":
                    flag = node["flag_if_no"]
                    # trata dicts e valores simples
                    if isinstance(flag, dict):
                        for fkey, fvalue in flag.items():
                            self.flags[fkey] = fvalue
                            log_action('flag_activated_no', {
                                'node': current,
                                'flag': fkey,
                                'value': fvalue
                            })
                    else:
                        self.flags[flag] = 1
                        log_action('flag_activated_no', {
                            'node': current,
                            'flag': flag
                        })
                
                if "flag_if_yes" in node and answer_clean == "sim":
                    flag = node["flag_if_yes"]
                    if isinstance(flag, dict):
                        for fkey, fvalue in flag.items():
                            self.flags[fkey] = fvalue
                            log_action('flag_activated_yes', {
                                'node': current,
                                'flag': fkey,
                                'value': fvalue
                            })
                    else:
                        self.flags[flag] = 1
                        log_action('flag_activated_yes', {
                            'node': current,
                            'flag': flag
                        })
                
                if "flag_if" in node:
                    if isinstance(node["flag_if"], dict) and answer_clean in node["flag_if"]:
                        for key_flag, value_flag in node["flag_if"][answer_clean].items():
                            self.flags[key_flag] = value_flag
                            log_action('flag_set_answer', {
                                'node': current,
                                'answer': answer_clean,
                                'flag': key_flag,
                                'value': value_flag
                            })
                
                # Verificação de chaves dinâmicas para nós padrão
                for key in node:
                    if key.startswith("flag_if_") and key != "flag_if":
                        expected_option = key[len("flag_if_"):].strip().lower()
                        if answer_clean == expected_option:
                            flag_val = node[key]
                            if isinstance(flag_val, dict):
                                for fkey, fvalue in flag_val.items():
                                    self.flags[fkey] = fvalue
                                    log_action('flag_set_dynamic', {
                                        'node': current,
                                        'answer': answer_clean,
                                        'flag': fkey,
                                        'value': fvalue
                                    })
                            else:
                                self.flags[flag_val] = 1
                                log_action('flag_activated_dynamic', {
                                    'node': current,
                                    'answer': answer_clean,
                                    'flag': flag_val
                                })
                
                if "flag_if_no_condition" in node and answer_clean == "não":
                    condition = node["flag_if_no_condition"]
                    field_value = str(self.data.get(condition["field"], "")).lower()
                    
                    if "local" in field_value:
                        self.flags[condition["local"]] = 1
                        log_action('flag_activated_condition_local', {
                            'node': current,
                            'flag': condition["local"]
                        })
                    elif "remoto" in field_value:
                        self.flags[condition["remoto"]] = 1
                        log_action('flag_activated_condition_remoto', {
                            'node': current,
                            'flag': condition["remoto"]
                        })
                
                if "flag_if_sim_condition" in node and answer_clean == "sim":
                    condition = node["flag_if_sim_condition"]
                    try:
                        field_value = float(self.data.get(condition["field"], 0))
                        if field_value > condition.get("greater_than", 0):
                            self.flags[condition["flag"]] = 1
                            log_action('flag_activated_condition_sim', {
                                'node': current,
                                'flag': condition["flag"],
                                'field': condition["field"],
                                'value': field_value,
                                'threshold': condition.get("greater_than", 0)
                            })
                    except (ValueError, TypeError):
                        pass
                
                # Verifica se houve flags acionadas após esta resposta
                flags_antes = self.flags.copy()
                
                # Compara e registra pendência se alguma flag nova foi ativada
                flags_depois = self.flags
                if current != "tela_aviso":
                    novas_flags = [k for k in flags_depois if flags_depois[k] and not flags_antes.get(k)]
                    for flag in novas_flags:
                        # Adiciona a flag específica à lista de pendências
                        # Apenas se a flag causar indeferimento
                        flag_info = self.flags_manager.get_flag_info(flag)
                        if flag_info and flag_info.get('indeferimento', True):
                            self.pendencias.append(flag)
                            
                # acrescentar isto IMEDIATAMENTE antes de processar o next_key genérico:
                if current == "potencia":
                    # só entra aqui se responderam “Sim” ou “Não” à potência
                    if answer_clean == "sim":
                        try:
                            val = float(self.data.get("CCSP_POTMICROGER", 0))
                        except:
                            val = 0
                        if val > 7.5:
                            # # avisa o usuário e leva direto a fast_track_supera
                            QMessageBox.warning(
                                self.parent,
                                "Aviso",
                                "Cliente não pode selecionar opções de Fast Track (itens 4.5 no anexo)!"
                            )
                            current = "fast_track_supera"
                        else:
                            # segue para Fast Track normal
                            current = "fast_track"
                    else:
                            try:
                                val = float(self.data.get("CCSP_POTMICROGER", 0))
                            except:
                                val = 0
                        # respondeu “Não”
                                                    # ativa a flag 28
                            self.flags[30] = 1
                            log_action('flag_activated_sim_potencia_gt', {
                                'node': current, 'flag': 30, 'value': val
                            })
                            # avisa o usuário e leva direto a fast_track_supera
                            QMessageBox.warning(
                                self.parent,
                                "Aviso",
                                "Cliente não pode selecionar opções de Fast Track (itens 4.5 no anexo)!"
                            )

                            if val > 7.5:

                                current = "fast_track_supera"
                            else:
                                # segue para Fast Track normal
                                current = "fast_track"
                    continue   # vai para o próximo loop já usando o next_key correto
                
                if current == "fast_track_supera":
                    # só entra aqui se responderam “Sim” ou “Não” à potência
                    if answer_clean == "sim" and str(self.data.get("MOD_PP", "")).strip().lower() == "autoconsumo local":
                            self.flags[28] = 1
                            log_action('flag_activated_fast_track_supera', {
                                'node': current, 'flag': 31, 'value': val
                            })
                            current = "art_91_comum"
                    elif answer_clean == "sim" and str(self.data.get("MOD_PP", "")).strip().lower() == "autoconsumo remoto":
                            self.flags[31] = 1
                            self.flags[28] = 1
                            log_action('flag_activated_fast_track_supera', {
                                'node': current, 'flag': 31, 'value': val
                            })
                            log_action('flag_activated_fast_track_supera', {
                                'node': current, 'flag': 28, 'value': val
                            })
                            current = "art_91_comum"
                    else:
                        current = "art_91_comum"
                    continue   # vai para o próximo loop já usando o next_key correto
                            
                if current == "itens_obrigatorios_comum":
                    mod_pp = str(self.data.get("MOD_PP", "")).strip().lower()
                    if mod_pp == "autoconsumo remoto":
                        from app.ui.modulo_rateio import abrir_tela_beneficiarias_rateio
                        beneficiarias, rateios = abrir_tela_beneficiarias_rateio()
                        self.data["beneficiarias"] = beneficiarias
                        self.data["rateios"] = rateios
                        
                                # ——— Novo bloco de consulta HANA e flags ———
                        from app.database.hana_connector import consultar_uc_hana

                        for uc_code in beneficiarias:
                            uc_info = consultar_uc_hana(uc_code)
                            if uc_info.get("CONCESSAO", "").strip().upper() != "CPFL PAULISTA":
                                print(uc_info.get("CONCESSAO", "").strip().upper())
                                self.flags[8] = 1
                                log_action('flag_activated_hana', {'flag': 8, 'uc': uc_code})
                            check1 = uc_info.get("COD_TIPO_INSTALACAO", "").strip().upper()
                            if uc_info.get("COD_TIPO_INSTALACAO", "").strip().upper() == "B OPTANTE":
                                self.flags[9] = 1
                                log_action('flag_activated_hana', {'flag': 9, 'uc': uc_code})
                            check = uc_info.get("STATUS_INSTALACAO", "").strip().upper()
                            if uc_info.get("STATUS_INSTALACAO", "").strip().upper() != "NÃO SUSPENSA":
                                print(uc_info.get("STATUS_INSTALACAO", "").strip().upper())
                                self.flags[10] = 1
                                log_action('flag_activated_hana', {'flag': 10, 'uc': uc_code})
                            tipo = self.data.get("TIPO_DOCUMENTO", "").upper()
                            num_doc = self.data.get("NUMERO_DOC", "").strip().upper()
                            if tipo == "PF":
                                if tipo != uc_info.get("TIPO_DOCUMENTO", "").strip().upper():
                                    self.flags[11] = 1
                                    log_action('flag_activated_hana', {'flag': 11, 'uc': uc_code})
                                else:
                                    if num_doc != uc_info.get("NUMERO_DOC", ""):
                                        self.flags[11] = 1
                                        log_action('flag_activated_hana', {'flag': 11, 'uc': uc_code})
                            
                            if tipo == "PJ":
                                if tipo != uc_info.get("TIPO_DOCUMENTO", "").strip().upper():
                                    self.flags[11] = 1
                                    log_action('flag_activated_hana', {'flag': 11, 'uc': uc_code})
                                else:
                                    try:
                                        str_cnpj_1 = str(int(num_doc)).zfill(14)
                                        str_cnpj_2 = str(int(uc_info.get("NUMERO_DOC", ""))).zfill(14)
                                        if str_cnpj_1[:-6] != str_cnpj_2[:-6]:
                                            self.flags[11] = 1
                                            log_action('flag_activated_hana', {'flag': 11, 'uc': uc_code})
                                    except (ValueError, TypeError):
                                        self.flags[11] = 1
                                        log_action('flag_activated_hana', {'flag': 11, 'uc': uc_code})
                                        

                        total_rateio = sum(rateios or [])
                        if abs(total_rateio - 100) > 1e-6:
                            self.flags[12] = 1
                            log_action('flag_activated_rateio', {'flag': 12, 'total_rateio': total_rateio})
                                        
                                
                # Determina o próximo nó
                next_key_data = node["responses"].get(answer_clean)
                if isinstance(next_key_data, dict):
                    tipo_doc = self.history.get("tipo_documento", "").lower()
                    next_key = next_key_data.get(tipo_doc, None)
                else:
                    next_key = next_key_data
                
                current = next_key
                
            except Exception as e:
                # Log do erro
                error_msg = f"Erro ao processar pergunta '{current}': {str(e)}\n{traceback.format_exc()}"
                print(error_msg)
                log_action('decision_tree_error', {'error': str(e), 'node': current})
                
                # Exibe mensagem de erro para o usuário
                QMessageBox.critical(
                    self.parent,
                    "Erro na Árvore de Decisão",
                    f"Ocorreu um erro ao processar a pergunta:\n{str(e)}\n\nA análise será interrompida."
                )
                
                # Interrompe a execução da árvore
                break
        
        # Emite sinal de conclusão da análise
        if hasattr(self, 'analysis_completed') and self.analysis_completed is not None:
            self.analysis_completed.emit()

        if self.flags_manager:
            for flag_id, value in self.flags.items():
                if value:
                    self.flags_manager.set_flag(flag_id, value)
        
        return self.history, self.pendencias
    
    def get_active_flags(self):
        """
        Retorna as flags ativas.
        
        Returns:
            dict: Dicionário com as flags ativas.
        """
        return {k: v for k, v in self.flags.items() if v}
    
    def get_history(self):
        """
        Retorna o histórico de respostas.
        
        Returns:
            dict: Histórico de respostas.
        """
        return self.history
    
    def get_pendencias(self):
        """
        Retorna a lista de pendências.
        
        Returns:
            list: Lista de pendências.
        """
        return self.pendencias
