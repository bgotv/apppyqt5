# app/automation/web_automation.py

import os
import time
import tempfile
import shutil
import subprocess
import re
import logging
import sys
import requests

from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from selenium.common.exceptions import SessionNotCreatedException, NoSuchElementException, StaleElementReferenceException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from webdriver_manager.microsoft import EdgeChromiumDriverManager

from app.utils.logger import log_action
from app.utils.performance import PerformanceTracker

logger = logging.getLogger("web_automation")


def obter_versao_edge():
    """Retorna a versão principal do Microsoft Edge instalada, ex: '138'"""
    try:
        result = subprocess.run(
            ["reg", "query", r"HKEY_CURRENT_USER\Software\Microsoft\Edge\BLBeacon", "/v", "version"],
            capture_output=True, text=True, shell=True
        )
        match = re.search(r"version\s+REG_SZ\s+([\d.]+)", result.stdout)
        if match:
            return match.group(1).split(".")[0]
    except Exception as e:
        log_action("edge_version_error", {"error": str(e)})
    return None


def obter_driver_edge(downloads_folder):
    """
    Tenta cinco estratégias para instanciar um EdgeDriver compatível:
      1) copia de instantclient_23_7 -> raiz do exe
      2) WEBDRIVER-MANAGER com novo blob.core.windows.net
      3) driver local na raiz
      4) webdriver-manager padrão
      5) Selenium Manager
    Retorna (driver, temp_profile_dir)
    """
    logger.info("==== Iniciando obter_driver_edge ====")
    options = Options()
    options.add_experimental_option("prefs", {
        "download.default_directory": downloads_folder,
        "download.prompt_for_download": False,
        "directory_upgrade": True,
    })
    temp_profile = tempfile.mkdtemp(prefix="edge_profile_")
    options.add_argument(f"--user-data-dir={temp_profile}")

    # determina pasta do executável ou do módulo
    if getattr(sys, "frozen", False):
        exec_dir = os.path.dirname(sys.executable)
    else:
        exec_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    root_driver = os.path.join(exec_dir, "msedgedrivers.exe")
    ic_driver   = os.path.join(exec_dir, "instantclient_23_7", "msedgedrivers.exe")

    logger.info(f"Exec dir: {exec_dir}")
    logger.info(f"Driver raiz esperado: {root_driver}")
    logger.info(f"Driver instantclient: {ic_driver}")

    versao_edge = obter_versao_edge()
    logger.info(f"Versão do Edge detectada: {versao_edge}")
    log_action("edge_version_detected", {"version": versao_edge})

    # 1) copiar de instantclient se compatível
    if os.path.exists(ic_driver):
        try:
            temp_driver = webdriver.Edge(service=Service(ic_driver), options=options)
            drv_ver = temp_driver.capabilities.get("browserVersion", "")
            temp_driver.quit()
            if versao_edge and drv_ver.startswith(versao_edge):
                if not os.path.exists(root_driver):
                    shutil.copy2(ic_driver, root_driver)
                    logger.info(f"Copiado driver para raiz: {root_driver}")
        except Exception as e:
            logger.warning(f"Driver instantclient não compatível: {e}")

    # 2) WEBDRIVER-MANAGER COM ENDPOINTS ATUALIZADOS
    try:
        url_versao = (
            "https://msedgewebdriverstorage.blob.core.windows.net/edgewebdriver/"
            f"LATEST_RELEASE_{versao_edge}"
        )
        resp = requests.get(url_versao)
        versao_completa = resp.text.strip()
    except Exception:
        versao_completa = None
    try:
        logger.info("Tentando WDM override com versão completa")
        mgr = EdgeChromiumDriverManager(
            version=versao_completa,
            url="https://msedgewebdriverstorage.blob.core.windows.net/edgewebdriver",
            latest_release_url="https://msedgewebdriverstorage.blob.core.windows.net/edgewebdriver/LATEST_STABLE"
        )
        mgr_path = mgr.install()
        return webdriver.Edge(service=Service(mgr_path), options=options), temp_profile
    except Exception as e:
        logger.warning(f"WDM override falhou: {e}")
        log_action("driver_wdm_override_fail", {"error": str(e)})

    # 3) tentar driver local na raiz
    if os.path.exists(root_driver):
        try:
            logger.info("Tentando driver local na raiz...")
            temp_driver = webdriver.Edge(service=Service(root_driver), options=options)
            drv_ver = temp_driver.capabilities.get("browserVersion", "")
            temp_driver.quit()
            logger.info(f"Versão do driver local: {drv_ver}")
            if versao_edge and not drv_ver.startswith(versao_edge):
                raise SessionNotCreatedException(f"Driver {drv_ver} != Edge {versao_edge}")
            log_action("driver_local_success", {"path": root_driver})
            return webdriver.Edge(service=Service(root_driver), options=options), temp_profile
        except SessionNotCreatedException as e:
            logger.error(f"Driver local incompatível: {e}")
            log_action("driver_local_incompatible", {"error": str(e)})
        except Exception as e:
            logger.error(f"Falha driver local: {e}")
            log_action("driver_local_fail", {"error": str(e)})
    else:
        logger.info("Driver local não encontrado, pulando para fallback")

    # 4) webdriver-manager padrão
    try:
        logger.info("Tentando webdriver-manager padrão...")
        mgr_path = EdgeChromiumDriverManager().install()
        logger.info(f"Driver baixado pelo WDM padrão: {mgr_path}")
        log_action("driver_wdm_success", {"path": mgr_path})
        return webdriver.Edge(service=Service(mgr_path), options=options), temp_profile
    except Exception as e:
        logger.error(f"WDM padrão falhou: {e}")
        log_action("driver_wdm_fail", {"error": str(e)})

    # 5) Selenium Manager (PATH)
    try:
        logger.info("Tentando Selenium Manager...")
        log_action("driver_select", {"method": "selenium_manager"})
        return webdriver.Edge(options=options), temp_profile
    except Exception as e:
        logger.error(f"Selenium Manager falhou: {e}")
        raise RuntimeError(f"Todos os métodos de EdgeDriver falharam: {e}")


def abrir_atividade(nota, cd_projeto):
    """
    Abre a atividade no site CPFL, extrai campos, baixa anexos,
    monta valores_site incluindo `anexos_por_categoria`.
    Retorna (downloads_folder, valores_site).
    """
    with PerformanceTracker("abrir_atividade") as tracker:
        downloads_folder = os.path.join(os.path.expanduser("~"), "Downloads", str(nota))
        os.makedirs(downloads_folder, exist_ok=True)
        log_action("folder_ready", {"path": downloads_folder})

        driver, temp_profile = obter_driver_edge(downloads_folder)
        try:
            driver.maximize_window()
            wait = WebDriverWait(driver, 55)

            # login / navegação
            driver.get(
                "https://cpflb2cprd.b2clogin.com/cpflb2cprd.onmicrosoft.com/"
                "b2c_1a_signup_signin_mfa_front/oauth2/v2.0/authorize?"
                "p=B2C_1A_SIGNUP_SIGNIN_MFA_FRONT&client_id=17d5831d-6741-4670-8085-"
                "d1d34e37aec1&nonce=defaultNonce&redirect_uri=https%3A//www.cpfl.com.br/"
                "b2c-auth/receive-token&scope=17d5831d-6741-4670-8085-d1d34e37aec1%20"
                "offline_access&response_type=code&prompt=login&response_mode=query"
            )
            wait.until(EC.element_to_be_clickable((By.ID, "AzureADCPFLHomologExchange"))).click()
            # corrigido XPath sem aspas extras
            wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(),'Olá')]") ))
            log_action("login_success", {})

            # detalhes do projeto
            driver.get(
                f"https://projetosparticulares.cpfl.com.br/Intranet/Projeto/Detalhes?"
                f"codigoProjeto={cd_projeto}&codigoSubgrupo=0&ig=0&podeMoverParaMeuInbox=False"
            )
            wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Detalhes do projeto')]") ))

            # scroll e extração
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)

            def safe(id_):
                try:
                    return wait.until(EC.presence_of_element_located((By.ID, id_))).get_attribute("value") or ""
                except:
                    return "Valor não encontrado"

            valores_site = {
                "qnt_mod_site": safe("CadastroAneel_QuantidadeDeModulos"),
                "qnt_inv_site": safe("CadastroAneel_QuantidadeDeInversores"),
                "potencia_total_mod_site": safe("CadastroAneel_PotenciaTotalDosModulos"),
                "modelo_mod_site": safe("CadastroAneel_ModeloDosModulos"),
                "modelo_inv_site": safe("CadastroAneel_ModeloDosInversores"),
                "potencia_total_inv_site": safe("CadastroAneel_PotenciaTotalDosInversores"),
                "campo_profissional_site": safe("NomeProfissional"),
            }
            nome = safe("NomeCliente"); sobrenome = safe("Sobrenome")
            valores_site["proprietario_site"] = f"{nome} {sobrenome}".strip() or "Valor não encontrado"

            # endereço
            rua = safe("item_Logradouro"); bairro = safe("item_Bairro")
            mun = safe("item_Municipio"); est = safe("item_Estado")
            valores_site["endereco_art_site"] = f"{rua}, {bairro}, {mun} - {est}".strip() or "Valor não encontrado"

            # coletar anexos por categoria
            categorias = {}
            for fs in driver.find_elements(By.CSS_SELECTOR, "fieldset.scheduler-border"):
                try:
                    cat = fs.find_element(By.TAG_NAME, "legend").text.strip()
                except:
                    cat = "Sem Categoria"
                arquivos = []
                for li in fs.find_elements(By.CSS_SELECTOR, "ol > li"):
                    try:
                        arquivos.append(li.find_element(By.TAG_NAME, "span").text.strip())
                    except:
                        pass
                if arquivos:
                    categorias[cat] = arquivos
            valores_site["anexos_por_categoria"] = categorias

            # baixar arquivos
            elems = wait.until(EC.presence_of_all_elements_located(
                (By.XPATH, "//*[@id='conteudo']//fieldset//ol/li/a/span")
            ))
            for e in elems:
                try:
                    driver.execute_script("arguments[0].scrollIntoView();", e)
                    time.sleep(0.3)
                    e.click()
                except Exception:
                    continue
            time.sleep(8)

            log_action("web_automation_success", {"nota": nota, "cd_projeto": cd_projeto})
            tracker.add_detail("downloads", os.listdir(downloads_folder))
            return downloads_folder, valores_site

        except Exception as e:
            log_action("web_automation_error", {"error": str(e)})
            raise
        finally:
            try:
                driver.quit()
            except:
                pass
            shutil.rmtree(temp_profile, ignore_errors=True)
