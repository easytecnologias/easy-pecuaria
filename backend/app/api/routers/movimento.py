import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import get_current_user, get_fazenda_no_escopo
from app.models.movimento import MovimentoAnimal
from app.models.rebanho import Animal
from app.models.usuario import Usuario
from app.schemas import ComposicaoRebanho, MovimentoAnimalIn, ResumoMovimentos
from app.services.movimento import (
    composicao_rebanho,
    registrar_movimento,
    resumo_movimentos,
)
from app.services.rebanho import recomputar_indicadores_rebanho

router = APIRouter(tags=["movimento"])

TIPOS = {"compra", "venda", "morte", "descarte", "transferencia"}


@router.get("/fazendas/{fazenda_id}/movimentos", response_model=ResumoMovimentos)
def resumo(
    fazenda_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
) -> dict:
    faz = get_fazenda_no_escopo(fazenda_id, db, user)
    return resumo_movimentos(db, faz)


@router.get("/fazendas/{fazenda_id}/rebanho-composicao", response_model=ComposicaoRebanho)
def composicao(
    fazenda_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
) -> dict:
    faz = get_fazenda_no_escopo(fazenda_id, db, user)
    return composicao_rebanho(db, faz)


@router.post("/animais/{animal_id}/movimentos", status_code=201)
def novo_movimento(
    animal_id: uuid.UUID,
    body: MovimentoAnimalIn,
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
) -> dict:
    if body.tipo not in TIPOS:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"tipo inválido (use: {', '.join(TIPOS)})")
    animal = db.get(Animal, animal_id)
    if animal is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Animal não encontrado")
    faz = get_fazenda_no_escopo(animal.fazenda_id, db, user)
    m = registrar_movimento(
        db, animal, body.tipo, body.data or date.today(), body.valor,
        body.motivo, body.lote_destino_id, body.observacao, usuario=user,
    )
    recomputar_indicadores_rebanho(db, faz)
    return {"ok": True, "id": str(m.id), "novo_status": animal.status}


@router.delete("/movimentos/{mov_id}", status_code=204)
def excluir_movimento(
    mov_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
) -> None:
    m = db.get(MovimentoAnimal, mov_id)
    if m is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Movimento não encontrado")
    get_fazenda_no_escopo(m.fazenda_id, db, user)
    db.delete(m)
    db.commit()
