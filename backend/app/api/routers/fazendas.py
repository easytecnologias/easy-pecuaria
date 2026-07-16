import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import fazendas_do_usuario, get_current_user, get_fazenda_no_escopo
from app.models.parametro import Parametro
from app.models.rebanho import Animal
from app.models.usuario import Usuario
from app.schemas import (
    FazendaIn,
    FazendaOut,
    FazendaUpdateIn,
    ParametroOut,
    ParametroUpdateIn,
)
from app.services.fazenda import criar_fazenda

router = APIRouter(prefix="/fazendas", tags=["fazendas"])


@router.get("", response_model=list[FazendaOut])
def listar_fazendas(
    db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)
) -> list[FazendaOut]:
    return fazendas_do_usuario(db, user)


@router.post("", response_model=FazendaOut, status_code=201)
def nova_fazenda(
    body: FazendaIn,
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
) -> FazendaOut:
    """Cria fazenda na organizacao do usuario, ja com as metas padrao."""
    faz = criar_fazenda(db, user.org_id, user.id, body.nome, body.municipio, body.uf)
    return faz


@router.put("/{fazenda_id}", response_model=FazendaOut)
def editar_fazenda(
    fazenda_id: uuid.UUID,
    body: FazendaUpdateIn,
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
) -> FazendaOut:
    faz = get_fazenda_no_escopo(fazenda_id, db, user)
    for campo, valor in body.model_dump(exclude_unset=True).items():
        setattr(faz, campo, valor)
    db.commit()
    db.refresh(faz)
    return faz


@router.delete("/{fazenda_id}", status_code=204)
def excluir_fazenda(
    fazenda_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
) -> None:
    faz = get_fazenda_no_escopo(fazenda_id, db, user)
    n = db.execute(
        select(func.count(Animal.id)).where(Animal.fazenda_id == faz.id)
    ).scalar_one()
    if n > 0:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"A fazenda tem {n} animal(is). Exclua ou mova os animais antes de apagar a fazenda.",
        )
    db.delete(faz)
    db.commit()


@router.get("/{fazenda_id}/parametros", response_model=list[ParametroOut])
def parametros_da_fazenda(
    fazenda_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
) -> list[ParametroOut]:
    faz = get_fazenda_no_escopo(fazenda_id, db, user)
    return list(
        db.execute(
            select(Parametro).where(Parametro.fazenda_id == faz.id).order_by(Parametro.grupo, Parametro.rotulo)
        ).scalars().all()
    )


@router.put("/{fazenda_id}/parametros/{chave}", response_model=ParametroOut)
def atualizar_parametro(
    fazenda_id: uuid.UUID,
    chave: str,
    body: ParametroUpdateIn,
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
) -> ParametroOut:
    faz = get_fazenda_no_escopo(fazenda_id, db, user)
    param = db.execute(
        select(Parametro).where(Parametro.fazenda_id == faz.id, Parametro.chave == chave)
    ).scalar_one_or_none()
    if param is None:
        from fastapi import HTTPException, status

        raise HTTPException(status.HTTP_404_NOT_FOUND, "Parametro nao encontrado")
    param.valor = body.valor
    db.commit()
    db.refresh(param)
    return param
