"""
Análise de Notas Técnicas GD - Versão 2.0.0
Aplicativo para automatização da análise de notas técnicas de geração distribuída.

Desenvolvido por: Bruno Gobbi - CPFL Energia
"""

__version__ = "2.0.0"
__author__ = "Bruno Gobbi"
__email__ = "bgobbi@cpfl.com.br"
__license__ = "CPFL Energia - Uso Interno"

from src.config.settings import AppSettings

# Informações da aplicação
APP_NAME = AppSettings.APP_NAME
APP_VERSION = AppSettings.APP_VERSION

__all__ = [
    "__version__",
    "__author__", 
    "__email__",
    "APP_NAME",
    "APP_VERSION"
]