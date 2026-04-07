"""
Integração do Error Logger com FastAPI
Middlewares e Exception Handlers
"""

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable, Optional
import time
from .error_logger import (
    error_logger,
    LogLevel,
    LogObserverFactory
)


class ErrorLoggerMiddleware(BaseHTTPMiddleware):
    """
    Middleware para capturar e logar todas as exceptions
    """
    
    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            
            # Log HTTP error responses
            if response.status_code >= 400:
                error_logger.warning(
                    f"HTTP {response.status_code} response",
                    path=request.url.path,
                    method=request.method,
                    status_code=response.status_code
                )
            
            return response
        except Exception as exc:
            # Log unhandled exceptions
            error_logger.log_exception(
                exc,
                message="Unhandled exception in request",
                path=request.url.path,
                method=request.method,
                client_host=request.client.host if request.client else None
            )
            raise


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError
) -> JSONResponse:
    """Handler para erros de validação do Pydantic"""
    
    error_logger.warning(
        "Request validation failed",
        path=request.url.path,
        method=request.method,
        errors=exc.errors(),
        body=exc.body
    )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": exc.errors(),
            "body": exc.body
        }
    )


async def http_exception_handler(
    request: Request,
    exc: StarletteHTTPException
) -> JSONResponse:
    """Handler para HTTPException"""
    
    level = LogLevel.ERROR if exc.status_code >= 500 else LogLevel.WARNING
    
    error_logger.log(
        level,
        f"HTTP {exc.status_code}: {exc.detail}",
        path=request.url.path,
        method=request.method,
        status_code=exc.status_code
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )


async def general_exception_handler(
    request: Request,
    exc: Exception
) -> JSONResponse:
    """Handler genérico para todas as exceptions não tratadas"""
    
    error_logger.log_exception(
        exc,
        message="Unhandled exception",
        path=request.url.path,
        method=request.method,
        client_host=request.client.host if request.client else None
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"}
    )


def setup_error_logger(
    app: FastAPI,
    log_file: str = "logs/errors.log",
    enable_console: bool = True,
    enable_rotating: bool = True,
    log_format: str = "text",
    min_file_level: LogLevel = LogLevel.ERROR,
    min_console_level: LogLevel = LogLevel.WARNING,
    max_bytes: int = 10 * 1024 * 1024,
    backup_count: int = 5,
    register_handlers: bool = True,
    skip_middleware_registration: bool = False
) -> None:
    """
    Configura o error logger na aplicação FastAPI
    
    Args:
        app: Instância do FastAPI
        log_file: Caminho do arquivo de log
        enable_console: Habilita logging no console
        enable_rotating: Usa rotação de arquivos
        log_format: Formato do log ('text', 'json', 'compact')
        min_file_level: Nível mínimo para arquivo
        min_console_level: Nível mínimo para console
        max_bytes: Tamanho máximo do arquivo antes de rotacionar
        backup_count: Número de backups a manter
        register_handlers: Registra exception handlers automáticos
        skip_middleware_registration: Pula registro de middleware (útil se já foi registrado)
    """
    
    # Adiciona observer de arquivo
    if enable_rotating:
        file_observer = LogObserverFactory.create_rotating_file_observer(
            log_file,
            log_format,
            min_file_level,
            max_bytes,
            backup_count
        )
    else:
        file_observer = LogObserverFactory.create_file_observer(
            log_file,
            log_format,
            min_file_level
        )
    
    error_logger.attach(file_observer)
    
    # Adiciona observer de console
    if enable_console:
        console_observer = LogObserverFactory.create_console_observer(
            "compact",
            min_console_level
        )
        error_logger.attach(console_observer)
    
    # Registra exception handlers
    if register_handlers:
        app.add_exception_handler(
            RequestValidationError,
            validation_exception_handler
        )
        app.add_exception_handler(
            StarletteHTTPException,
            http_exception_handler
        )
        app.add_exception_handler(
            Exception,
            general_exception_handler
        )
    
    # Adiciona middleware (pode ser pulado se já foi registrado)
    if not skip_middleware_registration:
        app.add_middleware(ErrorLoggerMiddleware)
    
    # Log de inicialização
    error_logger.info(
        "Error logger initialized",
        log_file=log_file,
        log_format=log_format,
        rotating=enable_rotating
    )


class RequestLoggingMiddleware:
    """
    Middleware adicional para logar todas as requisições
    """
    
    def __init__(
        self,
        app: FastAPI,
        log_requests: bool = True,
        log_responses: bool = True
    ):
        self.app = app
        self.log_requests = log_requests
        self.log_responses = log_responses
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        request = Request(scope, receive)
        start_time = time.time()
        
        if self.log_requests:
            error_logger.debug(
                "Request received",
                method=request.method,
                path=request.url.path,
                query_params=str(request.query_params),
                client_host=request.client.host if request.client else None
            )
        
        status_code = None
        
        async def send_wrapper(message):
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
            await send(message)
        
        await self.app(scope, receive, send_wrapper)
        
        if self.log_responses:
            duration = time.time() - start_time
            error_logger.debug(
                "Request completed",
                method=request.method,
                path=request.url.path,
                status_code=status_code,
                duration_ms=round(duration * 1000, 2)
            )


def add_request_logging(
    app: FastAPI,
    log_requests: bool = True,
    log_responses: bool = True
) -> None:
    """
    Adiciona middleware de logging de requisições
    
    Args:
        app: Instância do FastAPI
        log_requests: Loga requisições recebidas
        log_responses: Loga respostas enviadas
    """
    app.middleware("http")(
        RequestLoggingMiddleware(app, log_requests, log_responses)
    )
