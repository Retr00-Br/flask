import os
from fastapi import FastAPI, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuração do caminho dos templates
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

def verify_supabase_connection():
    if supabase is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Conexão com o Supabase não inicializada."
        )

# Rota Principal serve a interface WEB
@app.get("/", response_class=HTMLResponse)
def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api/v1/pedidos/hoje", response_model=List[PedidoResponse])
def get_pedidos_hoje(data_consulta: Optional[date] = None):
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