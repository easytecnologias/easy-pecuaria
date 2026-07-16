import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import get_current_user, get_fazenda_no_escopo
from app.models.parto import Parto
from app.models.rebanho import Animal
from app.models.usuario import Usuario
from app.schemas import PartoIn, PartoOut, ResumoPartos
from app.services.parto import RESULTADOS, registrar_parto, resumo_partos
from app.services.rebanho import recomputar_indicadores_rebanho

router = APIRouter(tags=["partos"])


def _out(p: Parto, mae_brinco: str) -> PartoOut:
    return PartoOut(
        id=p.id, data=p.data, mae_id=p.mae_id, mae_brinco=mae_brinco,
        bezerro_id=p.bezerro_id, resultado=p.resultado, sexo_bezerro=p.sexo_bezerro,
        brinco_bezerro=p.brinco_bezerro,
        peso_nascimento=float(p.peso_nascimento) if p.peso_nascimento is not None else None,
        observacao=p.observacao,
    )


@router.get("/fazendas/{fazenda_id}/partos", response_model=ResumoPartos)
def resumo(
    fazenda_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
) -> ResumoPartos:
    faz = get_fazenda_no_escopo(fazenda_id, db, user)
    agg = resumo_partos(db, faz)
    linhas = db.execute(
        select(Parto, Animal.brinco)
        .join(Animal, Animal.id == Parto.mae_id)
        .where(Parto.fazenda_id == faz.id)
        .order_by(Parto.data.desc())
    ).all()
    return ResumoPartos(
        partos_12m=agg["partos_12m"], vivos_12m=agg["vivos_12m"],
        natimortos_12m=agg["natimortos_12m"], taxa_natimortalidade=agg["taxa_natimortalidade"],
        matrizes=agg["matrizes"], taxa_natalidade=agg["taxa_natalidade"],
        partos=[_out(p, brinco) for p, brinco in linhas],
    )


@router.post("/fazendas/{fazenda_id}/partos", response_model=PartoOut, status_code=201)
def novo_parto(
    fazenda_id: uuid.UUID,
    body: PartoIn,
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
) -> PartoOut:
    faz = get_fazenda_no_escopo(fazenda_id, db, user)
    if body.resultado not in RESULTADOS:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "resultado deve ser 'nascido_vivo' ou 'natimorto'")
    mae = db.get(Animal, body.mae_id)
    if mae is None or mae.fazenda_id != faz.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Matriz não encontrada nesta fazenda")
    if mae.sexo != "F":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "A mãe precisa ser uma fêmea")
    p = registrar_parto(
        db, faz, mae, body.data or date.today(), body.resultado,
        body.sexo_bezerro, body.brinco_bezerro, body.peso_nascimento, body.observacao,
    )
    return _out(p, mae.brinco)


@router.delete("/partos/{parto_id}", status_code=204)
def excluir_parto(
    parto_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
) -> None:
    p = db.get(Parto, parto_id)
    if p is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Parto não encontrado")
    faz = get_fazenda_no_escopo(p.fazenda_id, db, user)
    bezerro = db.get(Animal, p.bezerro_id) if p.bezerro_id else None
    db.delete(p)
    if bezerro is not None:
        db.delete(bezerro)  # remove o bezerro criado por este parto
    db.commit()
    recomputar_indicadores_rebanho(db, faz)
