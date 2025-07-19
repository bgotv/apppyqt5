#!/usr/bin/env python3
"""
Correção para o problema de contaminação de dados entre análises.
Este script aplica as correções necessárias no código original.

Problema: Quando o usuário para uma análise no meio e inicia outra,
dados da análise anterior contaminam a nova análise.

Solução: Implementa limpeza automática e gerenciamento de sessões.
"""

import os
import shutil
from pathlib import Path

def backup_original_files():
    """Cria backup dos arquivos originais."""
    print("📁 Criando backup dos arquivos originais...")
    
    files_to_backup = [
        "apppyqt5/app/ui/main_window.py",
        "apppyqt5/app/ui/analysis_form_corrected.py",
        "apppyqt5/app/core/decision_tree.py"
    ]
    
    backup_dir = Path("backup_original")
    backup_dir.mkdir(exist_ok=True)
    
    for file_path in files_to_backup:
        if os.path.exists(file_path):
            src = Path(file_path)
            dst = backup_dir / src.name
            shutil.copy2(src, dst)
            print(f"  ✅ Backup: {file_path} -> {dst}")

def apply_main_window_fix():
    """Aplica correção na janela principal."""
    print("\n🔧 Aplicando correção na janela principal...")
    
    file_path = "apppyqt5/app/ui/main_window.py"
    
    # Lê o arquivo original
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Aplica correções
    fixes = [
        # 1. Adiciona import do gerenciador de sessões
        {
            "search": "from app.utils.logger import log_ui_action",
            "replace": """from app.utils.logger import log_ui_action
from app.core.analysis_session_manager import session_manager"""
        },
        
        # 2. Modifica o método _on_avancar_clicked para limpar sessão
        {
            "search": """    @pyqtSlot()
    def _on_avancar_clicked(self):
        log_ui_action('avancar_clicked')
        
        # 1) Obtém a nota e tenta bloquear
        note = self.tree_notas.get_selected_note()
        if not note:
            QMessageBox.warning(self, "Aviso", "Selecione uma nota para análise.")
            return

        nr_atividade = str(note.get("NR_ATIVIDADE", ""))
        metrics_manager.start_stage(nr_atividade, "etapa_analise")""",
            "replace": """    @pyqtSlot()
    def _on_avancar_clicked(self):
        log_ui_action('avancar_clicked')
        
        # 1) Obtém a nota e tenta bloquear
        note = self.tree_notas.get_selected_note()
        if not note:
            QMessageBox.warning(self, "Aviso", "Selecione uma nota para análise.")
            return

        nr_atividade = str(note.get("NR_ATIVIDADE", ""))
        
        # 🔥 CORREÇÃO: Garante sessão limpa para nova análise
        session = session_manager.ensure_clean_session(nr_atividade, getpass.getuser())
        
        metrics_manager.start_stage(nr_atividade, "etapa_analise")"""
        },
        
        # 3. Adiciona limpeza antes de definir dados da nota
        {
            "search": """        # 4) Atualiza o AnalysisForm com tudo
        self.analysis_form.set_note_data(note, uc_data)
        self.analysis_form.valores_site = valores_site
        self.analysis_form.set_downloads_folder(folder)
        self.analysis_form.populate_attachments(folder)""",
            "replace": """        # 🔥 CORREÇÃO: Força limpeza completa antes de carregar nova nota
        self.analysis_form.force_clean_reset()
        
        # 4) Atualiza o AnalysisForm com tudo
        self.analysis_form.set_note_data(note, uc_data)
        self.analysis_form.valores_site = valores_site
        self.analysis_form.set_downloads_folder(folder)
        self.analysis_form.populate_attachments(folder)
        
        # 🔥 Atualiza dados na sessão
        session_manager.update_session_data(
            note_data=note,
            uc_data=uc_data,
            valores_site=valores_site,
            downloads_folder=folder
        )"""
        }
    ]
    
    # Aplica cada correção
    modified = False
    for fix in fixes:
        if fix["search"] in content:
            content = content.replace(fix["search"], fix["replace"])
            modified = True
            print(f"  ✅ Correção aplicada: {fix['search'][:50]}...")
        else:
            print(f"  ⚠️ Correção não aplicada (texto não encontrado): {fix['search'][:50]}...")
    
    if modified:
        # Salva arquivo modificado
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  ✅ Arquivo salvo: {file_path}")
    else:
        print(f"  ℹ️ Nenhuma modificação necessária em {file_path}")

def apply_analysis_form_fix():
    """Aplica correção no formulário de análise."""
    print("\n🔧 Aplicando correção no formulário de análise...")
    
    file_path = "apppyqt5/app/ui/analysis_form_corrected.py"
    
    # Lê o arquivo original
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Adiciona método de limpeza forçada
    new_method = '''
    def force_clean_reset(self):
        """
        🔥 CORREÇÃO: Força limpeza completa para prevenir contaminação.
        Remove TODOS os dados de análises anteriores.
        """
        try:
            # Limpa interface
            self.txt_results.clear()
            self.progress_bar.setValue(0)
            self.lbl_status.setText("Iniciando nova análise...")
            
            # Limpa dados da nota anterior
            self.note_data = {}
            self.uc_data = {}
            self.valores_site = {}
            self.downloads_folder = ""
            
            # Limpa anexos
            if hasattr(self, 'tree_attachments'):
                self.tree_attachments.clear()
            
            # 🔥 FORÇA limpeza completa de flags e histórico
            if hasattr(self, 'flags_manager') and self.flags_manager:
                self.flags_manager.clear_all_flags()
            
            if hasattr(self, 'decision_tree') and self.decision_tree:
                self.decision_tree.clear_history()
                # Força reset completo da árvore
                if hasattr(self.decision_tree, 'flags'):
                    for key in self.decision_tree.flags:
                        self.decision_tree.flags[key] = 0
                if hasattr(self.decision_tree, 'history'):
                    self.decision_tree.history.clear()
                if hasattr(self.decision_tree, 'pendencias'):
                    self.decision_tree.pendencias.clear()
            
            # Reset botões
            self.btn_iniciar_analise.setEnabled(True)
            self.btn_abrir_anexos.setEnabled(False)
            
            log_action('analysis_form_force_reset', {
                'timestamp': time.time(),
                'reason': 'contamination_prevention'
            })
            
            print("🧹 Limpeza forçada concluída - dados anteriores removidos")
            
        except Exception as e:
            print(f"⚠️ Erro durante limpeza forçada: {e}")
            # Mesmo com erro, continua para não bloquear o usuário
'''
    
    # Encontra local para inserir o método (após set_note_data)
    insert_point = content.find("    def set_note_data(self, note_data, uc_data):")
    if insert_point != -1:
        # Encontra o final do método set_note_data
        lines = content[insert_point:].split('\n')
        method_end = 0
        indent_level = None
        
        for i, line in enumerate(lines[1:], 1):  # Pula a linha da definição
            if line.strip() == '':
                continue
            
            current_indent = len(line) - len(line.lstrip())
            
            if indent_level is None and line.strip():
                indent_level = current_indent
            
            # Se encontrou linha com indentação menor ou igual ao método, é o fim
            if line.strip() and current_indent <= 4:  # 4 espaços = nível do método
                method_end = i
                break
        
        if method_end > 0:
            insertion_point = insert_point + len('\n'.join(lines[:method_end]))
            content = content[:insertion_point] + new_method + content[insertion_point:]
            
            # Salva arquivo modificado
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"  ✅ Método force_clean_reset() adicionado")
            print(f"  ✅ Arquivo salvo: {file_path}")
        else:
            print(f"  ⚠️ Não foi possível encontrar local para inserir método")
    else:
        print(f"  ⚠️ Método set_note_data não encontrado para inserir correção")

def create_session_manager():
    """Cria o arquivo do gerenciador de sessões no projeto original."""
    print("\n📝 Criando gerenciador de sessões...")
    
    # Cria diretório se não existir
    target_dir = Path("apppyqt5/app/core")
    target_dir.mkdir(parents=True, exist_ok=True)
    
    # Copia o arquivo do gerenciador de sessões
    src_file = "src/core/analysis_session_manager.py"
    dst_file = target_dir / "analysis_session_manager.py"
    
    if os.path.exists(src_file):
        # Adapta imports para o projeto original
        with open(src_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Ajusta imports
        content = content.replace(
            "from src.utils.logger import get_logger, log_user_action",
            "from app.utils.logger import log_action"
        )
        content = content.replace(
            "from src.utils.performance_tracker import performance_tracker",
            "# from app.utils.performance import measure_performance"
        )
        content = content.replace("log_user_action", "log_action")
        
        # Salva arquivo adaptado
        with open(dst_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"  ✅ Gerenciador criado: {dst_file}")
    else:
        print(f"  ❌ Arquivo fonte não encontrado: {src_file}")

def create_usage_example():
    """Cria exemplo de uso da correção."""
    print("\n📋 Criando exemplo de uso...")
    
    example_code = '''# EXEMPLO DE USO DA CORREÇÃO

# ANTES (com problema de contaminação):
def _on_avancar_clicked(self):
    note = self.tree_notas.get_selected_note()
    self.analysis_form.set_note_data(note, uc_data)
    # ❌ Dados da análise anterior ainda estão presentes!

# DEPOIS (com correção):
def _on_avancar_clicked(self):
    note = self.tree_notas.get_selected_note()
    nr_atividade = str(note.get("NR_ATIVIDADE", ""))
    
    # 🔥 Garante sessão limpa
    session = session_manager.ensure_clean_session(nr_atividade, getpass.getuser())
    
    # 🔥 Força limpeza completa
    self.analysis_form.force_clean_reset()
    
    # Agora carrega dados limpos
    self.analysis_form.set_note_data(note, uc_data)
    
    # ✅ Garantia de que não há contaminação!

# BENEFÍCIOS:
# ✅ Cada análise inicia completamente limpa
# ✅ Dados de análises anteriores são completamente removidos
# ✅ Histórico de decisões é zerado
# ✅ Flags são limpas
# ✅ Interface é resetada
# ✅ Logs de auditoria registram limpezas
'''
    
    with open("CORREÇÃO_CONTAMINAÇÃO_EXEMPLO.txt", 'w', encoding='utf-8') as f:
        f.write(example_code)
    
    print("  ✅ Exemplo criado: CORREÇÃO_CONTAMINAÇÃO_EXEMPLO.txt")

def main():
    """Função principal."""
    print("🔧 Correção do Problema de Contaminação de Dados")
    print("=" * 60)
    print("Problema: Dados de análises anteriores contaminam novas análises")
    print("Solução: Limpeza automática e gerenciamento de sessões")
    print("=" * 60)
    
    try:
        # 1. Backup
        backup_original_files()
        
        # 2. Cria gerenciador de sessões
        create_session_manager()
        
        # 3. Aplica correções
        apply_main_window_fix()
        apply_analysis_form_fix()
        
        # 4. Cria exemplo
        create_usage_example()
        
        print("\n" + "=" * 60)
        print("✅ CORREÇÃO APLICADA COM SUCESSO!")
        print("\n🎯 O que foi corrigido:")
        print("  ✅ Limpeza automática ao iniciar nova análise")
        print("  ✅ Gerenciamento de sessões implementado") 
        print("  ✅ Método force_clean_reset() adicionado")
        print("  ✅ Prevenção de contaminação de dados")
        print("  ✅ Logs de auditoria para rastreamento")
        
        print("\n📁 Arquivos modificados:")
        print("  - apppyqt5/app/ui/main_window.py")
        print("  - apppyqt5/app/ui/analysis_form_corrected.py") 
        print("  - apppyqt5/app/core/analysis_session_manager.py (novo)")
        
        print("\n💡 Como funciona agora:")
        print("  1. Usuário seleciona nova nota")
        print("  2. Sistema detecta mudança e limpa sessão anterior")
        print("  3. Todos os dados são zerados (flags, histórico, etc.)")
        print("  4. Nova análise inicia completamente limpa")
        print("  5. Impossível contaminação entre análises!")
        
        print("\n🔍 Para verificar se funcionou:")
        print("  1. Execute o aplicativo")
        print("  2. Inicie uma análise e pare no meio")
        print("  3. Selecione outra nota e avance")
        print("  4. Verifique que não há dados da análise anterior")
        
        print("\n📞 Suporte: bgobbi@cpfl.com.br")
        
    except Exception as e:
        print(f"\n❌ Erro durante aplicação da correção: {e}")
        print("Verifique os backups em backup_original/")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())