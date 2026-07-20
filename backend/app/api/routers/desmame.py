import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import get_current_user, get_fazenda_no_escopo
from app.models.rebanho import Animal
from app.models.usuario import Usuario
from app.schemas import AnimalOut, DesmamaIn, ResumoDesmama
from app.services.desmame import (
    TIPOS_MATRIZ,
    bezerros_da_matriz,
    registrar_desmama,
    resumo_desmama,
)

router = APIRouter(tags=["desmame"])


@router.get("/fazendas/{fazenda_id}/desmame", response_model=ResumoDesmama)
def resumo(
    fazenda_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
) -> ResumoDesmama:
    faz = get_fazenda_no_escopo(fazenda_id, db, user)
    return ResumoDesmama(**resumo_desmama(db, faz))


@router.get("/tipos-matriz", response_model=list[str])
def tipos_matriz(user: Usuario = Depends(get_current_user)) -> list[str]:
    return list(TIPOS_MATRIZ)


@router.get("/animais/{animal_id}/bezerros", response_model=list[AnimalOut])
def bezerros(
    animal_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
) -> list[Animal]:
    animal = db.get(Animal, animal_id)
    if animal is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Animal nao encontrado")
    faz = get_fazenda_no_escopo(animal.fazenda_id, db, user)
    return bezerros_da_matriz(db, faz, animal)


@router.post("/animais/{animal_id}/desmama", response_model=AnimalOut)
def desmamar(
    animal_id: uuid.UUID,
    body: DesmamaIn,
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
) -> Animal:
    animal = db.get(Animal, animal_id)
    if animal is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Animal nao encontrado")
    get_fazenda_no_escopo(animal.fazenda_id, db, user)
    if body.peso <= 0:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "peso deve ser maior que zero")
    return registrar_desmama(db, animal, body.peso, body.data)
