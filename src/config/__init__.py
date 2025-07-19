"""
Módulo de configurações da aplicação.
"""

from .settings import (
    AppSettings,
    DatabaseSettings, 
    EmailSettings,
    UISettings,
    PerformanceSettings,
    WebSettings,
    ConfigManager,
    config_manager
)

__all__ = [
    "AppSettings",
    "DatabaseSettings",
    "EmailSettings", 
    "UISettings",
    "PerformanceSettings",
    "WebSettings",
    "ConfigManager",
    "config_manager"
]