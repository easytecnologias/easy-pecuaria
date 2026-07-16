import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import get_current_user, get_fazenda_no_escopo
from app.models.escore import EscoreCorporal
from app.models.rebanho import Animal
from app.models.usuario import Usuario
from app.schemas import EscoreHistItem, EscoreIn, ResumoEscore
from app.services.escore import registrar_escore, resumo_escore

router = APIRouter(tags=["escore"])


@router.get("/fazendas/{fazenda_id}/escore", response_model=ResumoEscore)
def resumo(
    fazenda_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
) -> ResumoEscore:
    faz = get_fazenda_no_escopo(fazenda_id, db, user)
    r = resumo_escore(db, faz)
    historico = [
        EscoreHistItem(
            id=e.id, animal_id=e.animal_id, brinco=brinco, categoria=categoria,
            data=e.data, escore=float(e.escore), observacao=e.observacao,
        )
        for e, brinco, categoria in r["historico"]
    ]
    return ResumoEscore(
        n_avaliados=r["n_avaliados"], media=r["media"], magras=r["magras"],
        ideais=r["ideais"], gordas=r["gordas"], pct_ideais=r["pct_ideais"],
        historico=historico,
    )


@router.post("/fazendas/{fazenda_id}/escore", response_model=EscoreHistItem, status_code=201)
def novo_escore(
    fazenda_id: uuid.UUID,
    body: EscoreIn,
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
) -> EscoreHistItem:
    faz = get_fazenda_no_escopo(fazenda_id, db, user)
    animal = db.get(Animal, body.animal_id)
    if animal is None or animal.fazenda_id != faz.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Animal não encontrado nesta fazenda")
    if not (1.0 <= body.escore <= 5.0):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Escore deve estar entre 1 e 5")
    ecc = registrar_escore(db, faz.id, animal.id, body.data or date.today(), body.escore, body.observacao)
    db.commit()
    db.refresh(ecc)
    return EscoreHistItem(
        id=ecc.id, animal_id=animal.id, brinco=animal.brinco, categoria=animal.categoria,
        data=ecc.data, escore=float(ecc.escore), observacao=ecc.observacao,
    )


@router.delete("/escore/{escore_id}", status_code=204)
def excluir_escore(
    escore_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
) -> None:
    ecc = db.get(EscoreCorporal, escore_id)
    if ecc is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Avaliação não encontrada")
    get_fazenda_no_escopo(ecc.fazenda_id, db, user)
    db.delete(ecc)
    db.commit()
