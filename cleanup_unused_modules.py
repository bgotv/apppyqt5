#!/usr/bin/env python3
"""
Script para identificar e remover módulos/bibliotecas não utilizados.
Análise GD v2.0.0 - Otimização de dependências
"""

import os
import ast
import sys
from pathlib import Path
from collections import defaultdict
from typing import Set, Dict, List

class ImportAnalyzer(ast.NodeVisitor):
    """Analisador de importações em código Python."""
    
    def __init__(self):
        self.imports = set()
        self.from_imports = defaultdict(set)
    
    def visit_Import(self, node):
        """Visita declarações import."""
        for alias in node.names:
            self.imports.add(alias.name.split('.')[0])
    
    def visit_ImportFrom(self, node):
        """Visita declarações from ... import."""
        if node.module:
            base_module = node.module.split('.')[0]
            self.imports.add(base_module)
            for alias in node.names:
                self.from_imports[node.module].add(alias.name)

def analyze_python_files(directory: Path) -> Dict[str, Set[str]]:
    """
    Analisa todos os arquivos Python em um diretório.
    
    Args:
        directory: Diretório para analisar
        
    Returns:
        Dicionário com módulos importados por arquivo
    """
    file_imports = {}
    
    for py_file in directory.rglob("*.py"):
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            analyzer = ImportAnalyzer()
            analyzer.visit(tree)
            
            file_imports[str(py_file.relative_to(directory))] = analyzer.imports
            
        except (SyntaxError, UnicodeDecodeError) as e:
            print(f"⚠️ Erro ao analisar {py_file}: {e}")
    
    return file_imports

def get_all_used_modules(file_imports: Dict[str, Set[str]]) -> Set[str]:
    """
    Obtém conjunto de todos os módulos utilizados.
    
    Args:
        file_imports: Dicionário com importações por arquivo
        
    Returns:
        Conjunto de módulos utilizados
    """
    all_modules = set()
    for imports in file_imports.values():
        all_modules.update(imports)
    
    return all_modules

def get_requirements_modules() -> Set[str]:
    """
    Extrai módulos listados no requirements.txt.
    
    Returns:
        Conjunto de módulos no requirements.txt
    """
    modules = set()
    
    requirements_files = ["requirements.txt", "requirements_optimized.txt"]
    
    for req_file in requirements_files:
        if os.path.exists(req_file):
            with open(req_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        # Extrai nome do módulo (remove versão)
                        module_name = line.split('>=')[0].split('==')[0].split('<')[0]
                        modules.add(module_name.lower())
    
    return modules

def map_package_names() -> Dict[str, str]:
    """
    Mapeia nomes de importação para nomes de pacotes no requirements.
    
    Returns:
        Dicionário de mapeamento
    """
    return {
        'PyQt5': 'pyqt5',
        'pandas': 'pandas',
        'numpy': 'numpy', 
        'psutil': 'psutil',
        'selenium': 'selenium',
        'requests': 'requests',
        'oracledb': 'oracledb',
        'hdbcli': 'hdbcli',
        'webdriver_manager': 'webdriver-manager',
        'pytest': 'pytest',
        'black': 'black',
        'flake8': 'flake8',
        'sphinx': 'sphinx'
    }

def analyze_unused_modules():
    """Analisa módulos não utilizados no projeto."""
    print("🔍 Analisando módulos não utilizados...")
    print("=" * 50)
    
    # Analisa arquivos Python
    project_root = Path(".")
    file_imports = analyze_python_files(project_root)
    
    # Obtém módulos utilizados
    used_modules = get_all_used_modules(file_imports)
    
    # Obtém módulos do requirements
    requirements_modules = get_requirements_modules()
    
    # Mapeia nomes
    package_mapping = map_package_names()
    
    # Mapeia módulos utilizados para nomes de pacotes
    used_packages = set()
    for module in used_modules:
        if module in package_mapping:
            used_packages.add(package_mapping[module])
        else:
            used_packages.add(module.lower())
    
    # Módulos não utilizados
    unused_modules = requirements_modules - used_packages
    
    # Módulos utilizados mas não listados
    missing_modules = used_packages - requirements_modules
    
    print("📊 Relatório de Análise:")
    print(f"  - Arquivos Python analisados: {len(file_imports)}")
    print(f"  - Módulos únicos importados: {len(used_modules)}")
    print(f"  - Pacotes no requirements: {len(requirements_modules)}")
    
    print("\n✅ Módulos UTILIZADOS:")
    for module in sorted(used_packages):
        if module in requirements_modules:
            print(f"  - {module}")
    
    if unused_modules:
        print("\n❌ Módulos NÃO UTILIZADOS (podem ser removidos):")
        for module in sorted(unused_modules):
            print(f"  - {module}")
    else:
        print("\n✅ Nenhum módulo não utilizado encontrado!")
    
    if missing_modules:
        print("\n⚠️ Módulos utilizados mas NÃO LISTADOS no requirements:")
        for module in sorted(missing_modules):
            if module not in ['src', 'pathlib', 'typing', 'dataclasses', 'contextmanager']:
                print(f"  - {module}")
    
    return used_packages, unused_modules, missing_modules

def generate_optimized_requirements(used_packages: Set[str]):
    """
    Gera arquivo requirements otimizado.
    
    Args:
        used_packages: Conjunto de pacotes utilizados
    """
    print("\n📝 Gerando requirements otimizado...")
    
    # Pacotes essenciais com versões
    essential_packages = {
        'pyqt5': 'PyQt5>=5.15.0',
        'pandas': 'pandas>=1.5.0',
        'pyarrow': 'pyarrow>=10.0.0',
        'oracledb': 'oracledb>=1.4.0',
        'hdbcli': 'hdbcli>=2.16.0',
        'psutil': 'psutil>=5.9.0',
        'selenium': 'selenium>=4.15.0',
        'webdriver-manager': 'webdriver-manager>=4.0.0',
        'requests': 'requests>=2.28.0'
    }
    
    # Pacotes opcionais
    optional_packages = {
        'pytest': 'pytest>=7.0.0',
        'black': 'black>=22.0.0',
        'flake8': 'flake8>=5.0.0',
        'sphinx': 'sphinx>=5.0.0'
    }
    
    with open('requirements_final.txt', 'w', encoding='utf-8') as f:
        f.write("# Análise GD v2.0.0 - Dependências Finais Otimizadas\n")
        f.write("# Contém apenas módulos realmente utilizados\n\n")
        
        f.write("# ===== DEPENDÊNCIAS ESSENCIAIS =====\n")
        for pkg_key, pkg_line in essential_packages.items():
            if pkg_key in used_packages or pkg_key.replace('-', '_') in used_packages:
                f.write(f"{pkg_line}\n")
        
        f.write("\n# ===== DEPENDÊNCIAS OPCIONAIS =====\n")
        f.write("# Descomente se necessário:\n")
        for pkg_key, pkg_line in optional_packages.items():
            if pkg_key in used_packages:
                f.write(f"{pkg_line}\n")
            else:
                f.write(f"# {pkg_line}\n")
    
    print("✅ Arquivo 'requirements_final.txt' criado!")

def show_detailed_usage():
    """Mostra uso detalhado por arquivo."""
    print("\n📋 Uso detalhado por arquivo:")
    print("=" * 50)
    
    project_root = Path(".")
    file_imports = analyze_python_files(project_root)
    
    for file_path, imports in sorted(file_imports.items()):
        if imports:  # Só mostra arquivos com importações
            print(f"\n📄 {file_path}:")
            for imp in sorted(imports):
                print(f"  - {imp}")

def main():
    """Função principal."""
    print("🧹 Análise GD v2.0.0 - Limpeza de Módulos Não Utilizados")
    print("=" * 60)
    
    try:
        # Análise principal
        used_packages, unused_modules, missing_modules = analyze_unused_modules()
        
        # Gera requirements otimizado
        generate_optimized_requirements(used_packages)
        
        # Mostra uso detalhado se solicitado
        if len(sys.argv) > 1 and sys.argv[1] == '--detailed':
            show_detailed_usage()
        
        print("\n" + "=" * 60)
        print("✅ Análise concluída!")
        
        if unused_modules:
            print(f"📈 Economia potencial: {len(unused_modules)} pacotes removidos")
        else:
            print("🎯 Projeto já otimizado - nenhum módulo desnecessário!")
        
        print("\n📁 Arquivos gerados:")
        print("  - requirements_final.txt (versão otimizada)")
        print("\n💡 Dica: Execute com --detailed para ver uso por arquivo")
        
    except Exception as e:
        print(f"❌ Erro durante análise: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())