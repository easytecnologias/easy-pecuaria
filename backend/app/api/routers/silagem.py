import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import get_current_user, get_fazenda_no_escopo
from app.models.silagem import TIPOS_SILAGEM, Silagem
from app.models.usuario import Usuario
from app.schemas import ResumoSilagem, SilagemIn, SilagemOut
from app.services.silagem import resumo

router = APIRouter(tags=["silagem"])


@router.get("/silagem/tipos", response_model=list[str])
def tipos(user: Usuario = Depends(get_current_user)) -> list[str]:
    return list(TIPOS_SILAGEM)


@router.get("/fazendas/{fazenda_id}/silagem", response_model=ResumoSilagem)
def listar_silagem(
    fazenda_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
) -> ResumoSilagem:
    faz = get_fazenda_no_escopo(fazenda_id, db, user)
    r = resumo(db, faz)
    return ResumoSilagem(
        **{k: v for k, v in r.items() if k != "silos"},
        silos=[SilagemOut.model_validate(s) for s in r["silos"]],
    )


@router.post("/fazendas/{fazenda_id}/silagem", response_model=SilagemOut, status_code=201)
def nova_silagem(
    fazenda_id: uuid.UUID,
    body: SilagemIn,
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
) -> Silagem:
    faz = get_fazenda_no_escopo(fazenda_id, db, user)
    if body.tipo not in TIPOS_SILAGEM:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, f"tipo invalido (use: {', '.join(TIPOS_SILAGEM)})"
        )
    s = Silagem(fazenda_id=faz.id, **body.model_dump())
    db.add(s)
    db.commit()
    db.refresh(s)
    return s


def _silo_no_escopo(silo_id: uuid.UUID, db: Session, user: Usuario) -> Silagem:
    s = db.get(Silagem, silo_id)
    if s is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Silagem nao encontrada")
    get_fazenda_no_escopo(s.fazenda_id, db, user)
    return s


@router.put("/silagem/{silo_id}", response_model=SilagemOut)
def editar_silagem(
    silo_id: uuid.UUID,
    body: SilagemIn,
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
) -> Silagem:
    s = _silo_no_escopo(silo_id, db, user)
    for campo, valor in body.model_dump().items():
        setattr(s, campo, valor)
    db.commit()
    db.refresh(s)
    return s


@router.delete("/silagem/{silo_id}", status_code=204)
def excluir_silagem(
    silo_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
) -> None:
    s = _silo_no_escopo(silo_id, db, user)
    db.delete(s)
    db.commit()
