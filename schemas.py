from pydantic import BaseModel
from datetime import date, time, datetime
from typing import Optional

class PedidoBase(BaseModel):
    numero_nf: Optional[float] = None
    numero_pv: float
    separador: Optional[str] = None
    data_pedido: date
    skus: Optional[int] = None
    tr_nc: Optional[str] = None
    status_producao: Optional[str] = None
    status: Optional[str] = None
    cliente: str

class PedidoEmergenciaUpdate(BaseModel):
    is_emergencia: bool
    solicitante_urgencia: str
    motivo_urgencia: str

class PedidoResponse(PedidoBase):
    id: int
    is_emergencia: bool
    solicitante_urgencia: Optional[str] = None
    motivo_urgencia: Optional[str] = None
    janela_inicio: Optional[time] = None
    janela_fim: Optional[time] = None
    farol_status: str  # "VERDE", "AMARELO", "VERMELHO" (calculado no backend)

    class Config:
        from_attributes = True

class DashboardKPIs(BaseModel):
    total_pedidos: int
    total_emergencias: int
    percentual_emergencias: float
    total_fora_sla: int
    total_em_producao: int