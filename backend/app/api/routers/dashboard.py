import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import fazendas_do_usuario, get_current_user, get_fazenda_no_escopo
from app.models.organizacao import Organizacao
from app.models.usuario import Usuario
from app.schemas import DashboardOut, EvolucaoRebanhoOut, FazendaPainelOut
from app.services.painel import evolucao_rebanho, montar_dashboard, montar_painel_fazenda

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("", response_model=DashboardOut)
def dashboard_consolidado(
    db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)
) -> DashboardOut:
    """Painel consolidado do grupo + cartoes por fazenda (no escopo do usuario)."""
    org = db.get(Organizacao, user.org_id)
    fazendas = fazendas_do_usuario(db, user)
    return montar_dashboard(db, org, fazendas)


@router.get("/evolucao", response_model=EvolucaoRebanhoOut)
def evolucao(
    db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)
) -> EvolucaoRebanhoOut:
    """Evolução do rebanho: nascimentos por mês (últimos 12 meses) no grupo."""
    fazendas = fazendas_do_usuario(db, user)
    return evolucao_rebanho(db, fazendas)


@router.get("/fazenda/{fazenda_id}", response_model=FazendaPainelOut)
def painel_fazenda(
    fazenda_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
) -> FazendaPainelOut:
    faz = get_fazenda_no_escopo(fazenda_id, db, user)
    return montar_painel_fazenda(db, faz)
