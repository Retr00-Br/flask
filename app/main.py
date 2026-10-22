from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from datetime import date
from typing import List, Optional

from app.database import supabase
from app.schemas import PedidoResponse, PedidoEmergenciaUpdate, DashboardKPIs

app = FastAPI(
    title="API de Produção e Logística",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configuração de CORS para permitir requisições do Frontend Vercel
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def verify_supabase_connection():
    """Valida se o cliente Supabase está instanciado antes das chamadas."""
    if supabase is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Conexão com o Supabase não inicializada. Verifique SUPABASE_URL e SUPABASE_KEY no painel da Vercel."
        )

@app.get("/")
def read_root():
    return {"status": "online", "message": "API da Operação em execução no Vercel!"}

@app.get("/api/v1/pedidos/hoje", response_model=List[PedidoResponse])
def get_pedidos_hoje(data_consulta: Optional[date] = None):
    """
    Retorna a lista de pedidos do dia (ou da data informada).
    Prioriza pedidos marcados como EMERGÊNCIA no topo.
    """
    verify_supabase_connection()
    target_date = (data_consulta or date.today()).isoformat()
    
    try:
        response = (
            supabase.table("pedidos")
            .select("*")
            .gte("data_pedido", f"{target_date}T00:00:00")
            .lte("data_pedido", f"{target_date}T23:59:59")
            .order("is_emergencia", ascending=False)
            .order("created_at", ascending=False)
            .execute()
        )
        
        pedidos = response.data or []
        
        for p in pedidos:
            p["farol_status"] = "VERDE"
            
        return pedidos
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar pedidos: {str(e)}")

@app.patch("/api/v1/pedidos/{pedido_id}/emergencia", response_model=PedidoResponse)
def marcar_emergencia(pedido_id: int, payload: PedidoEmergenciaUpdate):
    """
    Marca/Atualiza a ordem de urgência de um pedido com solicitante e motivo.
    """
    verify_supabase_connection()
    
    try:
        data_to_update = {
            "is_emergencia": payload.is_emergencia,
            "solicitante_urgencia": payload.solicitante_urgencia if payload.is_emergencia else None,
            "motivo_urgencia": payload.motivo_urgencia if payload.is_emergencia else None,
        }
        
        response = (
            supabase.table("pedidos")
            .update(data_to_update)
            .eq("id", pedido_id)
            .execute()
        )
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Pedido não encontrado")
            
        pedido = response.data[0]
        pedido["farol_status"] = "VERDE"
        return pedido
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao atualizar emergência: {str(e)}")

@app.get("/api/v1/dashboard/kpis", response_model=DashboardKPIs)
def get_kpis(data_consulta: Optional[date] = None):
    """
    Gera o resumo das métricas (KPIs) exibidas nos cards no topo do painel.
    """
    verify_supabase_connection()
    target_date = (data_consulta or date.today()).isoformat()
    
    try:
        response = (
            supabase.table("pedidos")
            .select("*")
            .gte("data_pedido", f"{target_date}T00:00:00")
            .lte("data_pedido", f"{target_date}T23:59:59")
            .execute()
        )
        
        pedidos = response.data or []
        total_pedidos = len(pedidos)
        
        emergencias = [p for p in pedidos if p.get("is_emergencia")]
        total_emergencias = len(emergencias)
        
        em_producao = [p for p in pedidos if p.get("status_producao") not in ["FATURADO", "CONCLUIDO"]]
        total_em_producao = len(em_producao)
        
        pct_emergencias = (total_emergencias / total_pedidos * 100) if total_pedidos > 0 else 0.0
        
        return {
            "total_pedidos": total_pedidos,
            "total_emergencias": total_emergencias,
            "percentual_emergencias": round(pct_emergencias, 2),
            "total_fora_sla": 0,
            "total_em_producao": total_em_producao
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao calcular KPIs: {str(e)}")