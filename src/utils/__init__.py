"""
Módulo de utilitários da aplicação.
"""

from .logger import (
    get_logger,
    setup_logging,
    log_user_action,
    log_decision_tree_action,
    log_report_generation,
    log_email_sent,
    log_database_operation,
    audit_logger
)

from .performance_tracker import (
    PerformanceTracker,
    performance_tracker,
    track_performance,
    measure_performance,
    StageTracker
)

from .error_handler import (
    ErrorHandler,
    setup_exception_handling
)

__all__ = [
    # Logger
    "get_logger",
    "setup_logging", 
    "log_user_action",
    "log_decision_tree_action",
    "log_report_generation",
    "log_email_sent",
    "log_database_operation",
    "audit_logger",
    
    # Performance
    "PerformanceTracker",
    "performance_tracker",
    "track_performance", 
    "measure_performance",
    "StageTracker",
    
    # Error handling
    "ErrorHandler",
    "setup_exception_handling"
]