import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import get_current_user, get_fazenda_no_escopo
from app.models.rebanho import Animal
from app.models.sanitario import EventoSanitario
from app.models.usuario import Usuario
from app.schemas import AplicacaoIn, ResumoSanitario
from app.services.sanitario import registrar_aplicacao, resumo_sanitario

router = APIRouter(tags=["sanitario"])


@router.get("/fazendas/{fazenda_id}/sanitario", response_model=ResumoSanitario)
def resumo(
    fazenda_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
) -> dict:
    faz = get_fazenda_no_escopo(fazenda_id, db, user)
    return resumo_sanitario(db, faz)


@router.post("/fazendas/{fazenda_id}/sanitario/aplicacoes", status_code=201)
def nova_aplicacao(
    fazenda_id: uuid.UUID,
    body: AplicacaoIn,
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
) -> dict:
    faz = get_fazenda_no_escopo(fazenda_id, db, user)
    # resolve alvo: um animal ou o lote inteiro
    if body.lote_id:
        animal_ids = list(db.execute(
            select(Animal.id).where(
                Animal.fazenda_id == faz.id, Animal.lote_id == body.lote_id,
                Animal.status == "ativo",
            )
        ).scalars().all())
    elif body.animal_id:
        animal_ids = [body.animal_id]
    else:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Informe um animal ou um lote")
    if not animal_ids:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Nenhum animal no alvo selecionado")

    n = registrar_aplicacao(
        db, faz.id, animal_ids, body.lote_id, body.tipo, body.produto,
        body.data or date.today(), body.proxima_aplicacao, body.dose, body.observacao,
    )
    return {"ok": True, "animais": n}


@router.delete("/sanitario/{evento_id}", status_code=204)
def excluir_evento(
    evento_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
) -> None:
    ev = db.get(EventoSanitario, evento_id)
    if ev is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Evento não encontrado")
    get_fazenda_no_escopo(ev.fazenda_id, db, user)
    db.delete(ev)
    db.commit()
