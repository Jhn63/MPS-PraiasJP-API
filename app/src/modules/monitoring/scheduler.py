import asyncio
from sqlalchemy.orm import Session
from database.db import SessionLocal
from models.estacao_model import EstacaoMonitoramento
from modules.monitoring.monitoring import MonitoramentoService

async def start_monitoring_loop(interval_seconds: int = 15):
    """
    Função assíncrona que roda infinitamente pausando por 'interval_seconds'.
    Em produção, você pode alterar esse valor para algo como 3 * 60 * 60 (3 horas).
    """
    print(f"[Agendador] Iniciando loop automático de monitoramento a cada {interval_seconds} segundos...")
    
    service = MonitoramentoService()
    
    while True:
        try:
            print("\n[Agendador] Iniciando ciclo de varredura...")
            
            # Abre conexão nova pro ciclo atual
            db: Session = SessionLocal()
            try:
                # Pega todas as estações (Atenção: em caso de muitas estações usar paginação)
                estacoes = db.query(EstacaoMonitoramento).all()
                if not estacoes:
                    print("[Agendador] Nenhuma estação localizada no banco.")
                
                for estacao in estacoes:
                    try:
                        # Roda a inteligência do fluxo
                        await service.monitorar_estacao(estacao.id, db)
                    except Exception as e_est:
                        print(f"[Agendador] Erro ao monitorar a estação ID {estacao.id}: {e_est}")
                        
            finally:
                db.close()
                
            print(f"[Agendador] Ciclo finalizado. Dormindo por {interval_seconds} segundos...")
            
        except Exception as e:
            print(f"[Agendador] Falha severa no ciclo: {e}")
            
        # Espera o tempo solicitado de forma assíncrona (não trava os outros requests do FastAPI)
        await asyncio.sleep(interval_seconds)
