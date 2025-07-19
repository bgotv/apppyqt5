"""
Configurações globais da aplicação reestruturada.
Versão aprimorada com melhor organização e validação.
"""

import os
from pathlib import Path
from dataclasses import dataclass
from typing import Optional
import json

# Diretório raiz do projeto
PROJECT_ROOT = Path(__file__).parent.parent.parent

@dataclass
class AppSettings:
    """Configurações principais da aplicação."""
    
    # Informações da aplicação
    APP_NAME: str = "Análise de Notas Técnicas GD"
    APP_VERSION: str = "2.0.0"
    APP_AUTHOR: str = "Bruno Gobbi - CPFL Energia"
    
    # Interface do usuário
    UI_STYLE: str = "Fusion"
    UI_THEME: str = "modern"
    WINDOW_MIN_WIDTH: int = 1200
    WINDOW_MIN_HEIGHT: int = 800
    
    # Diretórios
    BASE_DIR: Path = Path(r'\\pfl-cps-file\Divisao_GD\Data')
    DATA_DIR: Path = BASE_DIR / "data"
    LOGS_DIR: Path = DATA_DIR / "logs"
    PERFORMANCE_DIR: Path = DATA_DIR / "performance"
    TEMPLATES_DIR: Path = DATA_DIR / "templates"
    CACHE_DIR: Path = DATA_DIR / "cache"
    DOWNLOADS_DIR: Path = Path.home() / "Downloads" / "Anexos_GD"
    
    # Configurações de rede e sincronização
    NETWORK_ROOT: Path = Path(r"\\pfl-cps-file\Divisao_GD\web_automation_pp")
    SYNC_DB_PATH: Path = NETWORK_ROOT / "dados_sync.db"
    SYNC_INTERVAL_MINUTES: int = 30
    
    @classmethod
    def initialize_directories(cls):
        """Cria todos os diretórios necessários."""
        directories = [
            cls.DATA_DIR,
            cls.LOGS_DIR,
            cls.PERFORMANCE_DIR,
            cls.TEMPLATES_DIR,
            cls.CACHE_DIR,
            cls.DOWNLOADS_DIR,
            cls.NETWORK_ROOT
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

@dataclass
class DatabaseSettings:
    """Configurações de banco de dados."""
    
    # Oracle
    ORACLE_USER: str = "PPAPRT_AUT"
    ORACLE_PASSWORD: str = "FFG926Y99"
    ORACLE_DSN: str = "192.168.35.221:1535/ppartp.cpfl.com.br"
    ORACLE_POOL_MIN: int = 1
    ORACLE_POOL_MAX: int = 5
    ORACLE_TIMEOUT: int = 30
    
    # SAP HANA
    HANA_USER: str = "2006428"
    HANA_PASSWORD: str = "L8y#Bg*1259"
    HANA_ADDRESS: str = "cpspddhdb01"
    HANA_PORT: str = "31015"
    HANA_TIMEOUT: int = 30
    
    @classmethod
    def get_oracle_connection_string(cls) -> str:
        """Retorna string de conexão Oracle."""
        return f"{cls.ORACLE_USER}/{cls.ORACLE_PASSWORD}@{cls.ORACLE_DSN}"
    
    @classmethod
    def get_hana_connection_params(cls) -> dict:
        """Retorna parâmetros de conexão HANA."""
        return {
            "address": cls.HANA_ADDRESS,
            "port": cls.HANA_PORT,
            "user": cls.HANA_USER,
            "password": cls.HANA_PASSWORD
        }

@dataclass
class EmailSettings:
    """Configurações de e-mail."""
    
    POWER_AUTOMATE_URL: str = (
        "https://prod-129.westus.logic.azure.com:443/workflows/"
        "daf1c6a57aa44912970a3097c3deb4c5/triggers/manual/paths/invoke"
        "?api-version=2016-06-01&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0"
        "&sig=-DbKRCsHVdwUHtqN4ZNsBnux1Q8gLjO997lH-DiqlyA"
    )
    SENDER_EMAIL: str = "projetoseletricosrge@cpfl.com.br"
    DEFAULT_RECIPIENT: str = "tecnicogdpaulista@cpfl.com.br"
    API_KEY: str = "MinhaChaveSecreta"
    TIMEOUT: int = 30

@dataclass
class UISettings:
    """Configurações específicas da interface."""
    
    # Cores do tema moderno
    PRIMARY_COLOR: str = "#2E86AB"
    SECONDARY_COLOR: str = "#A23B72"
    SUCCESS_COLOR: str = "#28A745"
    WARNING_COLOR: str = "#FFC107"
    ERROR_COLOR: str = "#DC3545"
    BACKGROUND_COLOR: str = "#F8F9FA"
    
    # Fontes
    DEFAULT_FONT_FAMILY: str = "Segoe UI"
    DEFAULT_FONT_SIZE: int = 10
    TITLE_FONT_SIZE: int = 14
    HEADER_FONT_SIZE: int = 12
    
    # Animações
    ANIMATION_DURATION: int = 300
    ENABLE_ANIMATIONS: bool = True
    
    # Layout
    DEFAULT_MARGIN: int = 10
    DEFAULT_SPACING: int = 5
    WIDGET_PADDING: int = 8

@dataclass
class PerformanceSettings:
    """Configurações de performance e monitoramento."""
    
    # Medição de tempo
    ENABLE_PERFORMANCE_TRACKING: bool = True
    PERFORMANCE_LOG_LEVEL: str = "INFO"
    MAX_PERFORMANCE_RECORDS: int = 10000
    
    # Cache
    ENABLE_CACHING: bool = True
    CACHE_TTL_SECONDS: int = 3600  # 1 hora
    MAX_CACHE_SIZE_MB: int = 100
    
    # Timeouts
    DATABASE_TIMEOUT: int = 30
    WEB_REQUEST_TIMEOUT: int = 60
    FILE_OPERATION_TIMEOUT: int = 120

@dataclass
class WebSettings:
    """Configurações para automação web."""
    
    # URLs importantes
    CPFL_SITE_URL: str = "https://www.cpfl.com.br/mini-e-microgeracao"
    INMETRO_SITE_URL: str = "https://registro.inmetro.gov.br/consulta"
    CREA_SP_URL: str = "https://creanet1.creasp.org.br/index.aspx"
    
    # Configurações do navegador
    BROWSER_TIMEOUT: int = 30
    IMPLICIT_WAIT: int = 10
    PAGE_LOAD_TIMEOUT: int = 30
    HEADLESS_MODE: bool = False
    
    # Downloads
    DOWNLOAD_TIMEOUT: int = 300  # 5 minutos
    MAX_DOWNLOAD_SIZE_MB: int = 500

class ConfigManager:
    """Gerenciador de configurações com suporte a arquivo de configuração."""
    
    def __init__(self, config_file: Optional[Path] = None):
        """
        Inicializa o gerenciador de configurações.
        
        Args:
            config_file: Caminho para arquivo de configuração personalizado
        """
        self.config_file = config_file or (PROJECT_ROOT / "config.json")
        self._load_custom_config()
    
    def _load_custom_config(self):
        """Carrega configurações personalizadas do arquivo JSON."""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    custom_config = json.load(f)
                
                # Aplica configurações personalizadas
                self._apply_custom_config(custom_config)
                
            except Exception as e:
                print(f"Erro ao carregar configurações personalizadas: {e}")
    
    def _apply_custom_config(self, config: dict):
        """Aplica configurações personalizadas às classes de configuração."""
        for section_name, section_config in config.items():
            if hasattr(globals(), section_name):
                section_class = globals()[section_name]
                for key, value in section_config.items():
                    if hasattr(section_class, key):
                        setattr(section_class, key, value)
    
    def save_config(self):
        """Salva configurações atuais no arquivo JSON."""
        config = {
            "AppSettings": self._dataclass_to_dict(AppSettings),
            "DatabaseSettings": self._dataclass_to_dict(DatabaseSettings),
            "EmailSettings": self._dataclass_to_dict(EmailSettings),
            "UISettings": self._dataclass_to_dict(UISettings),
            "PerformanceSettings": self._dataclass_to_dict(PerformanceSettings),
            "WebSettings": self._dataclass_to_dict(WebSettings)
        }
        
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, default=str)
    
    @staticmethod
    def _dataclass_to_dict(dataclass_instance) -> dict:
        """Converte dataclass para dicionário."""
        return {
            field: getattr(dataclass_instance, field)
            for field in dataclass_instance.__annotations__
            if not field.startswith('_')
        }

# Inicializa configurações
config_manager = ConfigManager()

# Cria diretórios necessários
AppSettings.initialize_directories()

# Exporta configurações principais
__all__ = [
    'AppSettings',
    'DatabaseSettings',
    'EmailSettings',
    'UISettings',
    'PerformanceSettings',
    'WebSettings',
    'ConfigManager',
    'config_manager'
]