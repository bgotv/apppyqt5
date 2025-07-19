#!/usr/bin/env python3
"""
Demonstração das funcionalidades da versão 2.0.0 do Análise GD.
Este arquivo mostra como usar os novos recursos de performance e auditoria.
"""

import time
from datetime import datetime
from src.utils.performance_tracker import track_performance, performance_tracker
from src.utils.logger import get_logger, log_user_action, audit_logger

# Configura logging
logger = get_logger(__name__)

def demo_performance_tracking():
    """Demonstra o sistema de medição de performance."""
    print("🚀 Demonstração - Sistema de Performance")
    print("=" * 50)
    
    # Exemplo 1: Medição básica
    with track_performance("demo_operation") as tracker:
        print("Executando operação simulada...")
        time.sleep(2)  # Simula processamento
        
        # Adiciona detalhes durante a execução
        tracker.add_detail("items_processed", 100)
        tracker.add_detail("operation_type", "simulation")
    
    # Exemplo 2: Múltiplas operações
    operations = ["load_data", "process_data", "save_results"]
    
    for operation in operations:
        with track_performance(operation):
            print(f"Executando: {operation}")
            time.sleep(1)  # Simula processamento
    
    # Mostra estatísticas
    print("\n📊 Estatísticas de Performance:")
    for operation in ["demo_operation"] + operations:
        stats = performance_tracker.get_statistics(operation)
        if stats:
            print(f"  {operation}:")
            print(f"    - Execuções: {stats['count']}")
            print(f"    - Tempo médio: {stats['avg_duration']:.3f}s")
            print(f"    - Tempo total: {stats['total_duration']:.3f}s")

def demo_audit_logging():
    """Demonstra o sistema de auditoria."""
    print("\n🔍 Demonstração - Sistema de Auditoria")
    print("=" * 50)
    
    # Registra algumas ações
    actions = [
        ("user_login", {"ip": "192.168.1.100"}),
        ("note_selected", {"note_id": "12345"}, "12345"),
        ("question_answered", {"question": "tipo_documento", "answer": "pf"}, "12345"),
        ("report_generated", {"type": "deferido"}, "12345")
    ]
    
    for action, details, *note_id in actions:
        note_id = note_id[0] if note_id else None
        log_user_action(action, details, note_id)
        print(f"✅ Ação registrada: {action}")
        time.sleep(0.5)
    
    # Mostra relatório de auditoria
    print("\n📋 Relatório de Auditoria:")
    report = audit_logger.generate_report()
    
    print(f"  - Total de entradas: {report['summary']['total_entries']}")
    print(f"  - Usuários únicos: {report['summary']['unique_users']}")
    print(f"  - Ações únicas: {report['summary']['unique_actions']}")
    print(f"  - Notas analisadas: {report['summary']['notes_analyzed']}")
    
    print("\n📝 Ações registradas:")
    for action, count in report['actions'].items():
        print(f"  - {action}: {count}x")

def demo_error_handling():
    """Demonstra o sistema de tratamento de erros."""
    print("\n⚠️ Demonstração - Tratamento de Erros")
    print("=" * 50)
    
    from src.utils.error_handler import ErrorHandler
    
    error_handler = ErrorHandler()
    
    # Simula alguns erros
    try:
        # Erro simulado
        raise ValueError("Erro de demonstração")
    except Exception as e:
        error_handler.handle_error("demo_component", e, {
            "context": "demonstração",
            "timestamp": datetime.now().isoformat()
        }, show_user=False)
        print("✅ Erro tratado e registrado")

def demo_export_data():
    """Demonstra exportação de dados."""
    print("\n💾 Demonstração - Exportação de Dados")
    print("=" * 50)
    
    try:
        # Exporta métricas de performance
        json_file = performance_tracker.export_to_json()
        print(f"✅ Métricas exportadas (JSON): {json_file}")
        
        # Tenta exportar para Parquet (pode falhar se pandas não estiver disponível)
        try:
            parquet_file = performance_tracker.export_to_parquet()
            print(f"✅ Métricas exportadas (Parquet): {parquet_file}")
        except Exception as e:
            print(f"⚠️ Exportação Parquet falhou: {e}")
            
    except Exception as e:
        print(f"❌ Erro na exportação: {e}")

def demo_report_generation():
    """Demonstra geração de relatório completo."""
    print("\n📊 Demonstração - Relatório Completo")
    print("=" * 50)
    
    # Gera relatório de performance
    report = performance_tracker.generate_report()
    
    print("📈 Resumo da Sessão:")
    print(f"  - Duração: {report['summary']['session_duration']:.2f}s")
    print(f"  - Total de operações: {report['summary']['total_operations']}")
    print(f"  - Operações únicas: {report['summary']['unique_operations']}")
    
    print("\n💻 Informações do Sistema:")
    sys_info = report['system_info']
    print(f"  - CPUs: {sys_info['cpu_count']}")
    print(f"  - Memória total: {sys_info['memory_total']:.1f} GB")
    print(f"  - Memória disponível: {sys_info['memory_available']:.1f} GB")
    print(f"  - Memória do processo: {sys_info['process_memory']:.1f} MB")

def main():
    """Função principal da demonstração."""
    print("🎯 Análise GD v2.0.0 - Demonstração de Funcionalidades")
    print("=" * 60)
    print(f"Iniciado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Executa demonstrações
    demos = [
        demo_performance_tracking,
        demo_audit_logging,
        demo_error_handling,
        demo_export_data,
        demo_report_generation
    ]
    
    for demo in demos:
        try:
            demo()
        except Exception as e:
            print(f"❌ Erro na demonstração {demo.__name__}: {e}")
        
        print()  # Linha em branco entre demonstrações
    
    print("=" * 60)
    print("✅ Demonstração concluída!")
    print("📋 Arquivos gerados na pasta 'data/'")
    print("📞 Suporte: bgobbi@cpfl.com.br")

if __name__ == "__main__":
    main()