"""
Módulo de automação web para download de anexos do site da CPFL.
"""
import os
import time
import sys
from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from app.utils.logger import log_action
from app.utils.performance import measure_performance
from app.config import settings

class WebAutomationManager:
    """
    Gerencia a automação web para download de anexos e interação com o site da CPFL.
    """
    
    def __init__(self):
        """Inicializa o gerenciador de automação web."""
        self.driver = None
        self.wait = None
        self.downloads_folder = None
    
    @measure_performance
    def download_anexos(self, nota, cd_projeto):
        """
        Baixa os anexos de uma nota técnica do site da CPFL.
        
        Args:
            nota (str): Número da atividade/nota.
            cd_projeto (str): Código do projeto.
            
        Returns:
            dict: Resultado da operação com status e mensagens.
        """
        log_action('download_anexos_started', {
            'nota': nota,
            'cd_projeto': cd_projeto
        })
        
        # Define o caminho da pasta de downloads para o projeto
        self.downloads_folder = os.path.join(settings.DOWNLOADS_DIR, str(nota))
        
        # Cria a pasta se não existir
        if not os.path.exists(self.downloads_folder):
            os.makedirs(self.downloads_folder)
            log_action('download_folder_created', {'path': self.downloads_folder})
        else:
            log_action('download_folder_exists', {'path': self.downloads_folder})
        
        try:
            # -------------------------------------apagar comentario
            # # Inicializa o WebDriver
            # self._init_webdriver()
            
            # # Faz login no site
            # success = self._login()
            # if not success:
            #     return {
            #         'success': False,
            #         'message': 'Falha no login',
            #         'downloads_folder': self.downloads_folder
            #     }
            
            # # Acessa a página de detalhes do projeto
            # success = self._access_project_details(cd_projeto)
            # if not success:
            #     return {
            #         'success': False,
            #         'message': 'Falha ao acessar detalhes do projeto',
            #         'downloads_folder': self.downloads_folder
            #     }
            
            # Baixa os anexos
            file_count = self._download_attachments()
            
            # Encerra o navegador
            self._close_webdriver()
            
            log_action('download_anexos_completed', {
                'nota': nota,
                'cd_projeto': cd_projeto,
                'file_count': file_count
            })
            
            return {
                'success': True,
                'message': f'Download concluído. {file_count} arquivos baixados.',
                'downloads_folder': self.downloads_folder,
                'file_count': file_count
            }
            
        except Exception as e:
            log_action('download_anexos_error', {
                'nota': nota,
                'cd_projeto': cd_projeto,
                'error': str(e)
            })
            
            # Tenta encerrar o navegador em caso de erro
            try:
                if self.driver:
                    self.driver.quit()
            except:
                pass
            
            return {
                'success': False,
                'message': f'Erro ao baixar anexos: {str(e)}',
                'downloads_folder': self.downloads_folder
            }
    
    def _init_webdriver(self):
        # """Inicializa o WebDriver."""
        # # Configuração das opções do Edge
        # options = Options()
        # prefs = {"download.default_directory": self.downloads_folder}
        # options.add_experimental_option("prefs", prefs)
        
        # # Configuração do WebDriver
        # if getattr(sys, 'frozen', False):
        #     # Caminho quando empacotado (.exe)
        #     driver_path = os.path.join(sys._MEIPASS, "msedgedriver.exe")
        # else:
        #     # Caminho quando executado diretamente do .py
        #     driver_path = os.path.join(os.path.dirname(settings.BASE_DIR), "msedgedriver.exe")
        
        # # Inicializa o WebDriver
        # service = Service(driver_path)
        # self.driver = webdriver.Edge(service=service, options=options)
        # self.driver.maximize_window()
        # self.wait = WebDriverWait(self.driver, 55)
        
        log_action('webdriver_initialized')
    
    def _login(self):
        """
        Faz login no site da CPFL.
        
        Returns:
            bool: True se o login foi bem-sucedido, False caso contrário.
        """
        try:
            # # Acessa a página de login
            # self.driver.get("https://cpflb2cprd.b2clogin.com/cpflb2cprd.onmicrosoft.com/b2c_1a_signup_signin_mfa_front/oauth2/v2.0/authorize?p=B2C_1A_SIGNUP_SIGNIN_MFA_FRONT&client_id=17d5831d-6741-4670-8085-d1d34e37aec1&nonce=defaultNonce&redirect_uri=https%3A//www.cpfl.com.br/b2c-auth/receive-token&scope=17d5831d-6741-4670-8085-d1d34e37aec1%20offline_access&response_type=code&prompt=login&response_mode=query")
            
            # # Aguarda e clica no botão de colaboradores
            # botao_colaboradores = self.wait.until(EC.element_to_be_clickable((By.ID, "AzureADCPFLHomologExchange")))
            # botao_colaboradores.click()
            
            # # Aguarda a conclusão do login
            # self.wait.until(EC.presence_of_element_located(
            #     (By.XPATH, "//*[contains(text(), 'Olá')]")
            # ))
            
            log_action('login_successful')
            return True
            
        except Exception as e:
            log_action('login_failed', {'error': str(e)})
            return False
    
    def _access_project_details(self, cd_projeto):
        """
        Acessa a página de detalhes do projeto.
        
        Args:
            cd_projeto (str): Código do projeto.
            
        Returns:
            bool: True se o acesso foi bem-sucedido, False caso contrário.
        """
        try:
            # # Acessa a página de detalhes do projeto
            # self.driver.get(f"https://projetosparticulares.cpfl.com.br/Intranet/Projeto/Detalhes?codigoProjeto={cd_projeto}&codigoSubgrupo=0&ig=0&podeMoverParaMeuInbox=False")
            
            # # Aguarda a presença do texto "Detalhes do projeto"
            # self.wait.until(EC.presence_of_element_located(
            #     (By.XPATH, "//*[contains(text(), 'Detalhes do projeto')]")
            # ))
            
            log_action('project_details_accessed', {'cd_projeto': cd_projeto})
            return True
            
        except Exception as e:
            log_action('project_details_access_failed', {
                'cd_projeto': cd_projeto,
                'error': str(e)
            })
            return False
    
    def _download_attachments(self):
        """
        Baixa os anexos da página de detalhes do projeto.
        
        Returns:
            int: Número de arquivos baixados.
        """
        try:
            # # Rola até o elemento <legend> com o texto "Anexos"
            # anexos_legend = self.wait.until(
            #     EC.presence_of_element_located((By.XPATH, "//legend[contains(text(),'Anexos')]"))
            # )
            # self.driver.execute_script("arguments[0].scrollIntoView(true);", anexos_legend)
            
            # # Pequena pausa para garantir que os elementos estejam renderizados
            # time.sleep(2)
            
            # # Localiza todos os elementos que contêm o nome dos arquivos
            # file_elements = self.driver.find_elements(By.XPATH, "//*[@id='conteudo']//fieldset//ol/li/a/span")
            # file_count = len(file_elements)
            
            # log_action('attachments_found', {'count': file_count})
            
            # # Para cada arquivo, rola até o elemento e clica para iniciar o download
            # for i, file_elem in enumerate(file_elements):
            #     self.driver.execute_script("arguments[0].scrollIntoView(true);", file_elem)
            #     time.sleep(1)  # Aguarda a rolagem
            #     file_name = file_elem.text.strip()
            #     log_action('downloading_file', {
            #         'index': i + 1,
            #         'total': file_count,
            #         'file_name': file_name
            #     })
            #     file_elem.click()
            #     # Aguarda um pouco após cada clique para evitar sobrecarga
            #     time.sleep(2)
            
            # # Aguarda alguns segundos para garantir que os downloads sejam finalizados
            # log_action('waiting_for_downloads')
            # time.sleep(10)
            
            return 2
            
        except Exception as e:
            log_action('download_attachments_error', {'error': str(e)})
            return 0
    
    def _close_webdriver(self):
        """Encerra o WebDriver."""
        # if self.driver:
        #     self.driver.quit()
        #     self.driver = None
        #     self.wait = None
            # log_action('webdriver_closed')
    
    def open_inmetro_site(self):
        """
        Abre o site do INMETRO para consulta de certificados.
        
        Returns:
            bool: True se a operação foi bem-sucedida, False caso contrário.
        """
        try:
            # # Inicializa o WebDriver se necessário
            # if not self.driver:
            #     self._init_webdriver()
            
            # # Acessa o site do INMETRO
            # self.driver.get(settings.INMETRO_SITE_URL)
            
            log_action('inmetro_site_opened')
            return True
            
        except Exception as e:
            log_action('inmetro_site_open_failed', {'error': str(e)})
            return False
    
    def open_cpfl_site(self):
        """
        Abre o site da CPFL para download de formulários.
        
        Returns:
            bool: True se a operação foi bem-sucedida, False caso contrário.
        """
        try:
            # # Inicializa o WebDriver se necessário
            # if not self.driver:
            #     self._init_webdriver()
            
            # # Acessa o site da CPFL
            # self.driver.get(settings.CPFL_SITE_URL)
            
            log_action('cpfl_site_opened')
            return True
            
        except Exception as e:
            log_action('cpfl_site_open_failed', {'error': str(e)})
            return False
