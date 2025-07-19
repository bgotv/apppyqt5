#!/usr/bin/env python3
"""
Script de instalação e configuração do Análise GD v2.0.0
"""

import os
import sys
import subprocess
import json
from pathlib import Path

def check_python_version():
    """Verifica se a versão do Python é compatível."""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 ou superior é necessário.")
        print(f"   Versão atual: {sys.version}")
        return False
    
    print(f"✅ Python {sys.version.split()[0]} detectado")
    return True

def install_dependencies():
    """Instala as dependências do projeto."""
    print("\n📦 Instalando dependências...")
    
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ])
        print("✅ Dependências instaladas com sucesso")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro ao instalar dependências: {e}")
        return False

def create_directories():
    """Cria diretórios necessários."""
    print("\n📁 Criando diretórios...")
    
    directories = [
        "data/logs",
        "data/performance", 
        "data/cache",
        "data/templates",
        "config"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"   ✅ {directory}")
    
    print("✅ Diretórios criados")

def create_config_file():
    """Cria arquivo de configuração inicial."""
    print("\n⚙️ Criando arquivo de configuração...")
    
    config = {
        "AppSettings": {
            "APP_NAME": "Análise de Notas Técnicas GD",
            "APP_VERSION": "2.0.0",
            "WINDOW_MIN_WIDTH": 1200,
            "WINDOW_MIN_HEIGHT": 800
        },
        "DatabaseSettings": {
            "ORACLE_USER": "PPAPRT_AUT",
            "ORACLE_DSN": "192.168.35.221:1535/ppartp.cpfl.com.br",
            "HANA_USER": "2006428",
            "HANA_ADDRESS": "cpspddhdb01",
            "HANA_PORT": "31015"
        },
        "UISettings": {
            "PRIMARY_COLOR": "#2E86AB",
            "SECONDARY_COLOR": "#A23B72",
            "ENABLE_ANIMATIONS": True
        },
        "PerformanceSettings": {
            "ENABLE_PERFORMANCE_TRACKING": True,
            "MAX_PERFORMANCE_RECORDS": 10000
        }
    }
    
    config_file = Path("config.json")
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2)
    
    print("✅ Arquivo de configuração criado: config.json")
    print("   ⚠️ Lembre-se de configurar as senhas nos arquivos de configuração")

def test_imports():
    """Testa se as importações principais funcionam."""
    print("\n🧪 Testando importações...")
    
    test_modules = [
        "PyQt5.QtWidgets",
        "pandas", 
        "numpy",
        "psutil",
        "requests"
    ]
    
    failed_imports = []
    
    for module in test_modules:
        try:
            __import__(module)
            print(f"   ✅ {module}")
        except ImportError as e:
            print(f"   ❌ {module}: {e}")
            failed_imports.append(module)
    
    if failed_imports:
        print(f"\n❌ Falha ao importar: {', '.join(failed_imports)}")
        print("   Execute: pip install -r requirements.txt")
        return False
    
    print("✅ Todas as importações funcionaram")
    return True

def create_desktop_shortcut():
    """Cria atalho na área de trabalho (Windows)."""
    if os.name != 'nt':
        return
    
    try:
        import winshell
        from win32com.client import Dispatch
        
        desktop = winshell.desktop()
        path = os.path.join(desktop, "Análise GD v2.0.lnk")
        target = os.path.join(os.getcwd(), "main.py")
        wDir = os.getcwd()
        icon = target
        
        shell = Dispatch('WScript.Shell')
        shortcut = shell.CreateShortCut(path)
        shortcut.Targetpath = sys.executable
        shortcut.Arguments = f'"{target}"'
        shortcut.WorkingDirectory = wDir
        shortcut.IconLocation = icon
        shortcut.save()
        
        print("✅ Atalho criado na área de trabalho")
        
    except ImportError:
        print("   ⚠️ Módulos Windows não disponíveis para criar atalho")
    except Exception as e:
        print(f"   ⚠️ Erro ao criar atalho: {e}")

def main():
    """Função principal de instalação."""
    print("🚀 Instalação do Análise GD v2.0.0")
    print("=" * 50)
    
    # Verificações iniciais
    if not check_python_version():
        sys.exit(1)
    
    # Instalação
    steps = [
        create_directories,
        install_dependencies,
        create_config_file,
        test_imports,
        create_desktop_shortcut
    ]
    
    for step in steps:
        try:
            if not step():
                print(f"\n❌ Falha na etapa: {step.__name__}")
                sys.exit(1)
        except Exception as e:
            print(f"\n❌ Erro inesperado em {step.__name__}: {e}")
            sys.exit(1)
    
    # Finalização
    print("\n" + "=" * 50)
    print("🎉 Instalação concluída com sucesso!")
    print("\n📋 Próximos passos:")
    print("1. Configure as senhas no arquivo config.json")
    print("2. Verifique a conectividade de rede")
    print("3. Execute: python main.py")
    print("\n📞 Suporte: bgobbi@cpfl.com.br")

if __name__ == "__main__":
    main()