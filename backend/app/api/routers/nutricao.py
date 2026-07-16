import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import get_current_user, get_fazenda_no_escopo
from app.models.nutricao import Dieta, ItemDieta
from app.models.rebanho import Lote
from app.models.usuario import Usuario
from app.schemas import DietaIn, DietaOut, ItemDietaOut
from app.services.nutricao import calcular_dieta, recomputar_indicadores_dieta

router = APIRouter(tags=["nutricao"])


def _out(db: Session, dieta: Dieta) -> DietaOut:
    calc = calcular_dieta(db, dieta)
    lote_nome = None
    if dieta.lote_id:
        lote = db.get(Lote, dieta.lote_id)
        lote_nome = lote.nome if lote else None
    return DietaOut(
        id=dieta.id, nome=dieta.nome, lote_id=dieta.lote_id, lote_nome=lote_nome,
        data=dieta.data, ativa=dieta.ativa,
        itens=[ItemDietaOut.model_validate(i) for i in dieta.itens],
        custo_cab_dia=calc["custo_cab_dia"], consumo_ms_pv=calc["consumo_ms_pv"],
        kg_ms=calc["kg_ms"], peso_medio_lote=calc["peso_medio_lote"],
    )


@router.get("/fazendas/{fazenda_id}/dietas", response_model=list[DietaOut])
def listar_dietas(
    fazenda_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
) -> list[DietaOut]:
    faz = get_fazenda_no_escopo(fazenda_id, db, user)
    dietas = db.execute(
        select(Dieta).where(Dieta.fazenda_id == faz.id).order_by(Dieta.data.desc())
    ).scalars().all()
    return [_out(db, d) for d in dietas]


@router.post("/fazendas/{fazenda_id}/dietas", response_model=DietaOut, status_code=201)
def nova_dieta(
    fazenda_id: uuid.UUID,
    body: DietaIn,
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
) -> DietaOut:
    faz = get_fazenda_no_escopo(fazenda_id, db, user)
    if not body.itens:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "A dieta precisa de pelo menos um ingrediente")
    dieta = Dieta(fazenda_id=faz.id, nome=body.nome, lote_id=body.lote_id, data=date.today(), ativa=True)
    dieta.itens = [
        ItemDieta(ingrediente=i.ingrediente, inclusao_kg=i.inclusao_kg,
                  preco_kg=i.preco_kg, ms_pct=i.ms_pct)
        for i in body.itens
    ]
    db.add(dieta)
    db.commit()
    recomputar_indicadores_dieta(db, faz)
    db.refresh(dieta)
    return _out(db, dieta)


@router.delete("/dietas/{dieta_id}", status_code=204)
def excluir_dieta(
    dieta_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
) -> None:
    dieta = db.get(Dieta, dieta_id)
    if dieta is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Dieta não encontrada")
    faz = get_fazenda_no_escopo(dieta.fazenda_id, db, user)
    db.delete(dieta)
    db.commit()
    recomputar_indicadores_dieta(db, faz)
