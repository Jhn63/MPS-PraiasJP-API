"""
Módulo de Logger de Erros para FastAPI
Implementa os padrões: Observer, Singleton, Strategy e Factory
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime
from pathlib import Path
import json
import traceback
import logging
from enum import Enum
import threading


class LogLevel(Enum):
    """Níveis de log"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LogEntry:
    """Representa uma entrada de log estruturada"""
    
    def __init__(
        self,
        level: LogLevel,
        message: str,
        exception: Optional[Exception] = None,
        context: Optional[Dict[str, Any]] = None,
        timestamp: Optional[datetime] = None
    ):
        self.level = level
        self.message = message
        self.exception = exception
        self.context = context or {}
        self.timestamp = timestamp or datetime.now()
        self.traceback_str = None
        
        if exception:
            self.traceback_str = ''.join(
                traceback.format_exception(
                    type(exception),
                    exception,
                    exception.__traceback__
                )
            )
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte o log entry para dicionário"""
        data = {
            "timestamp": self.timestamp.isoformat(),
            "level": self.level.value,
            "message": self.message,
            "context": self.context
        }
        
        if self.exception:
            data["exception"] = {
                "type": type(self.exception).__name__,
                "message": str(self.exception),
                "traceback": self.traceback_str
            }
        
        return data
    
    def to_json(self) -> str:
        """Converte o log entry para JSON"""
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)


# PADRÃO OBSERVER
class LogObserver(ABC):
    """Interface Observer para observadores de log"""
    
    @abstractmethod
    def update(self, log_entry: LogEntry) -> None:
        """Recebe notificação de novo log entry"""
        pass


class LogSubject:
    """Subject do padrão Observer - gerencia observadores"""
    
    def __init__(self):
        self._observers: List[LogObserver] = []
        self._lock = threading.Lock()
    
    def attach(self, observer: LogObserver) -> None:
        """Adiciona um observador"""
        with self._lock:
            if observer not in self._observers:
                self._observers.append(observer)
    
    def detach(self, observer: LogObserver) -> None:
        """Remove um observador"""
        with self._lock:
            if observer in self._observers:
                self._observers.remove(observer)
    
    def notify(self, log_entry: LogEntry) -> None:
        """Notifica todos os observadores"""
        with self._lock:
            observers = self._observers.copy()
        
        for observer in observers:
            try:
                observer.update(log_entry)
            except Exception as e:
                # Evita que erro em um observer quebre outros
                print(f"Error in observer {observer.__class__.__name__}: {e}")


# PADRÃO STRATEGY - Estratégias de formatação
class LogFormatter(ABC):
    """Interface Strategy para formatação de logs"""
    
    @abstractmethod
    def format(self, log_entry: LogEntry) -> str:
        """Formata um log entry"""
        pass


class JSONFormatter(LogFormatter):
    """Formata logs como JSON"""
    
    def format(self, log_entry: LogEntry) -> str:
        return log_entry.to_json()


class TextFormatter(LogFormatter):
    """Formata logs como texto legível"""
    
    def format(self, log_entry: LogEntry) -> str:
        lines = [
            f"{'=' * 80}",
            f"[{log_entry.timestamp.strftime('%Y-%m-%d %H:%M:%S')}] {log_entry.level.value}",
            f"Message: {log_entry.message}",
        ]
        
        if log_entry.context:
            lines.append(f"Context: {json.dumps(log_entry.context, indent=2)}")
        
        if log_entry.exception:
            lines.extend([
                f"Exception: {type(log_entry.exception).__name__}",
                f"Details: {str(log_entry.exception)}",
                "Traceback:",
                log_entry.traceback_str
            ])
        
        lines.append(f"{'=' * 80}\n")
        return '\n'.join(lines)


class CompactFormatter(LogFormatter):
    """Formata logs de forma compacta (uma linha)"""
    
    def format(self, log_entry: LogEntry) -> str:
        timestamp = log_entry.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        exc_info = ""
        if log_entry.exception:
            exc_info = f" | {type(log_entry.exception).__name__}: {str(log_entry.exception)}"
        return f"[{timestamp}] {log_entry.level.value} - {log_entry.message}{exc_info}\n"


# IMPLEMENTAÇÕES DE OBSERVERS
class FileLogObserver(LogObserver):
    """Observer que escreve logs em arquivo"""
    
    def __init__(
        self,
        file_path: str,
        formatter: Optional[LogFormatter] = None,
        min_level: LogLevel = LogLevel.ERROR
    ):
        self.file_path = Path(file_path)
        self.formatter = formatter or TextFormatter()
        self.min_level = min_level
        self._lock = threading.Lock()
        
        # Cria diretório se não existir
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
    
    def update(self, log_entry: LogEntry) -> None:
        """Escreve log no arquivo"""
        # Filtra por nível
        level_priority = {
            LogLevel.DEBUG: 0,
            LogLevel.INFO: 1,
            LogLevel.WARNING: 2,
            LogLevel.ERROR: 3,
            LogLevel.CRITICAL: 4
        }
        
        if level_priority[log_entry.level] < level_priority[self.min_level]:
            return
        
        formatted_log = self.formatter.format(log_entry)
        
        with self._lock:
            with open(self.file_path, 'a', encoding='utf-8') as f:
                f.write(formatted_log)


class ConsoleLogObserver(LogObserver):
    """Observer que imprime logs no console"""
    
    def __init__(
        self,
        formatter: Optional[LogFormatter] = None,
        min_level: LogLevel = LogLevel.WARNING
    ):
        self.formatter = formatter or CompactFormatter()
        self.min_level = min_level
    
    def update(self, log_entry: LogEntry) -> None:
        """Imprime log no console"""
        level_priority = {
            LogLevel.DEBUG: 0,
            LogLevel.INFO: 1,
            LogLevel.WARNING: 2,
            LogLevel.ERROR: 3,
            LogLevel.CRITICAL: 4
        }
        
        if level_priority[log_entry.level] < level_priority[self.min_level]:
            return
        
        formatted_log = self.formatter.format(log_entry)
        print(formatted_log, end='')


class RotatingFileLogObserver(LogObserver):
    """Observer que escreve logs em arquivo com rotação automática"""
    
    def __init__(
        self,
        file_path: str,
        formatter: Optional[LogFormatter] = None,
        min_level: LogLevel = LogLevel.ERROR,
        max_bytes: int = 10 * 1024 * 1024,  # 10MB
        backup_count: int = 5
    ):
        self.file_path = Path(file_path)
        self.formatter = formatter or TextFormatter()
        self.min_level = min_level
        self.max_bytes = max_bytes
        self.backup_count = backup_count
        self._lock = threading.Lock()
        
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
    
    def _rotate(self) -> None:
        """Rotaciona os arquivos de log"""
        if not self.file_path.exists():
            return
        
        if self.file_path.stat().st_size < self.max_bytes:
            return
        
        # Remove o arquivo mais antigo
        oldest = self.file_path.with_suffix(f'.{self.backup_count}{self.file_path.suffix}')
        if oldest.exists():
            oldest.unlink()
        
        # Renomeia os arquivos existentes
        for i in range(self.backup_count - 1, 0, -1):
            src = self.file_path.with_suffix(f'.{i}{self.file_path.suffix}')
            dst = self.file_path.with_suffix(f'.{i + 1}{self.file_path.suffix}')
            if src.exists():
                src.rename(dst)
        
        # Renomeia o arquivo atual
        if self.file_path.exists():
            self.file_path.rename(
                self.file_path.with_suffix(f'.1{self.file_path.suffix}')
            )
    
    def update(self, log_entry: LogEntry) -> None:
        """Escreve log no arquivo com rotação"""
        level_priority = {
            LogLevel.DEBUG: 0,
            LogLevel.INFO: 1,
            LogLevel.WARNING: 2,
            LogLevel.ERROR: 3,
            LogLevel.CRITICAL: 4
        }
        
        if level_priority[log_entry.level] < level_priority[self.min_level]:
            return
        
        formatted_log = self.formatter.format(log_entry)
        
        with self._lock:
            self._rotate()
            with open(self.file_path, 'a', encoding='utf-8') as f:
                f.write(formatted_log)


# PADRÃO SINGLETON - Logger principal
class ErrorLoggerMeta(type):
    """Metaclass para implementar Singleton"""
    _instances = {}
    _lock = threading.Lock()
    
    def __call__(cls, *args, **kwargs):
        with cls._lock:
            if cls not in cls._instances:
                instance = super().__call__(*args, **kwargs)
                cls._instances[cls] = instance
        return cls._instances[cls]


class ErrorLogger(LogSubject, metaclass=ErrorLoggerMeta):
    """
    Logger principal de erros (Singleton)
    Implementa Observer pattern como Subject
    """
    
    def __init__(self):
        if not hasattr(self, '_initialized'):
            super().__init__()
            self._initialized = True
    
    def log(
        self,
        level: LogLevel,
        message: str,
        exception: Optional[Exception] = None,
        **context
    ) -> None:
        """Registra um log"""
        log_entry = LogEntry(
            level=level,
            message=message,
            exception=exception,
            context=context
        )
        self.notify(log_entry)
    
    def debug(self, message: str, **context) -> None:
        """Log de debug"""
        self.log(LogLevel.DEBUG, message, **context)
    
    def info(self, message: str, **context) -> None:
        """Log de informação"""
        self.log(LogLevel.INFO, message, **context)
    
    def warning(self, message: str, **context) -> None:
        """Log de aviso"""
        self.log(LogLevel.WARNING, message, **context)
    
    def error(
        self,
        message: str,
        exception: Optional[Exception] = None,
        **context
    ) -> None:
        """Log de erro"""
        self.log(LogLevel.ERROR, message, exception, **context)
    
    def critical(
        self,
        message: str,
        exception: Optional[Exception] = None,
        **context
    ) -> None:
        """Log crítico"""
        self.log(LogLevel.CRITICAL, message, exception, **context)
    
    def log_exception(
        self,
        exception: Exception,
        message: Optional[str] = None,
        **context
    ) -> None:
        """Log específico para exceptions"""
        msg = message or f"Exception occurred: {type(exception).__name__}"
        self.error(msg, exception, **context)


# PADRÃO FACTORY - Factory para criar observers pré-configurados
class LogObserverFactory:
    """Factory para criar observers de log"""
    
    @staticmethod
    def create_file_observer(
        file_path: str,
        format_type: str = "text",
        min_level: LogLevel = LogLevel.ERROR
    ) -> FileLogObserver:
        """Cria um FileLogObserver"""
        formatters = {
            "text": TextFormatter(),
            "json": JSONFormatter(),
            "compact": CompactFormatter()
        }
        
        formatter = formatters.get(format_type, TextFormatter())
        return FileLogObserver(file_path, formatter, min_level)
    
    @staticmethod
    def create_rotating_file_observer(
        file_path: str,
        format_type: str = "text",
        min_level: LogLevel = LogLevel.ERROR,
        max_bytes: int = 10 * 1024 * 1024,
        backup_count: int = 5
    ) -> RotatingFileLogObserver:
        """Cria um RotatingFileLogObserver"""
        formatters = {
            "text": TextFormatter(),
            "json": JSONFormatter(),
            "compact": CompactFormatter()
        }
        
        formatter = formatters.get(format_type, TextFormatter())
        return RotatingFileLogObserver(
            file_path,
            formatter,
            min_level,
            max_bytes,
            backup_count
        )
    
    @staticmethod
    def create_console_observer(
        format_type: str = "compact",
        min_level: LogLevel = LogLevel.WARNING
    ) -> ConsoleLogObserver:
        """Cria um ConsoleLogObserver"""
        formatters = {
            "text": TextFormatter(),
            "json": JSONFormatter(),
            "compact": CompactFormatter()
        }
        
        formatter = formatters.get(format_type, CompactFormatter())
        return ConsoleLogObserver(formatter, min_level)


# Instância global do logger (Singleton)
error_logger = ErrorLogger()
