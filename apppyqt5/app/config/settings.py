"""
Configurações globais da aplicação.
"""
import os

# Informações da aplicação
APP_NAME = "Análise de Ativides GD"
APP_VERSION = "0.0.5"
APP_STYLE = "Fusion"  # Estilo visual do Qt

# Diretórios da aplicação
BASE_DIR = r'\\pfl-cps-file\Divisao_GD\Data'
DATA_DIR = os.path.join(BASE_DIR, "data")
LOGS_DIR = os.path.join(DATA_DIR, "logs")
PERFORMANCE_DIR = os.path.join(DATA_DIR, "performance")
TEMPLATES_DIR = os.path.join(DATA_DIR, "templates")
DOWNLOADS_DIR = os.path.join(os.path.expanduser("~"), "Downloads", "Anexos_GD")

# Configurações de banco de dados Oracle
ORACLE_USER = "PPAPRT_AUT"
ORACLE_PASSWORD = "FFG926Y99"
ORACLE_DSN = "192.168.35.221:1535/ppartp.cpfl.com.br"

# Configurações de banco de dados SAP HANA
HANA_USER = "2006428"
HANA_PASSWORD = "L8y#Bg*1259"
HANA_ADDRESS = "cpspddhdb01"
HANA_PORT = "31015"

# Configurações de e-mail (Power Automate)
POWER_AUTOMATE_URL = ("https://prod-129.westus.logic.azure.com:443/workflows/daf1c6a57aa44912970a3097c3deb4c5/"
                      "triggers/manual/paths/invoke?api-version=2016-06-01&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=-DbKRCsHVdwUHtqN4ZNsBnux1Q8gLjO997lH-DiqlyA")
REMETENTE_FIXO = "projetoseletricosrge@cpfl.com.br"
API_KEY = "MinhaChaveSecreta"

# Arquivo de bloqueio de notas
LOCK_FILE_PATH = os.path.join(DATA_DIR, "LockedNotes.txt")

# URLs importantes
CPFL_SITE_URL = "https://www.cpfl.com.br/mini-e-microgeracao"
INMETRO_SITE_URL = "https://registro.inmetro.gov.br/consulta"
SITE_CREA_SP = "https://creanet1.creasp.org.br/index.aspx"

# endereço dados web pp
NETWORK_ROOT = r"\\pfl-cps-file\Divisao_GD\web_automation_pp"
DB_PATH      = os.path.join(NETWORK_ROOT, "dados_sync.db")

def configure_oracle_client():
    """
    Configura o Oracle Client para conexão com o banco de dados.
    
    Returns:
        str: Caminho para o Oracle Client.
    # """
    # # ⚠️ Força protocolo antigo compatível com Oracle 11g/12c para evitar ORA-28041
    # os.environ["ORA_SECURITY_VERSION"] = "11"
    # os.environ["ORA_CLIENT_VERIFIER"] = "0"

    # # Adiciona o instantclient à variável de ambiente PATH, apenas em tempo de execução

    # if getattr(sys, 'frozen', False):
    #     lib_path = os.path.join(os.path.dirname(sys.executable), "instantclient_23_7")
    # else:
    #     lib_path = os.path.join(os.path.dirname(__file__), "instantclient_23_7")

    # if hasattr(os, "add_dll_directory"):
    #     os.add_dll_directory(lib_path)

    # oracledb.init_oracle_client(lib_dir=lib_path)

    # # Ajuda o Windows a resolver dependências nativas como DLLs
    # if hasattr(os, "add_dll_directory"):
    #     os.add_dll_directory(lib_path)

    # oracledb.init_oracle_client(lib_dir=lib_path)
    
    # return lib_path

# Cria os diretórios necessários
os.makedirs(LOGS_DIR, exist_ok=True)
os.makedirs(PERFORMANCE_DIR, exist_ok=True)
os.makedirs(TEMPLATES_DIR, exist_ok=True)
os.makedirs(DOWNLOADS_DIR, exist_ok=True)
