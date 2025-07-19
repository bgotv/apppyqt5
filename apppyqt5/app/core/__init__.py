"""
Módulo core - Arquivo de inicialização.
"""
from app.core.flags_manager import FlagsManager
from app.core.report_generator import ReportGenerator
from app.core.decision_tree import DecisionTree

__all__ = ['FlagsManager', 'ReportGenerator', 'DecisionTree']
