import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import get_current_user, get_fazenda_no_escopo
from app.models.estoque import MovimentoVolumoso
from app.models.usuario import Usuario
from app.schemas import MovimentoIn, MovimentoOut, ResumoEstoque
from app.services.estoque import recomputar_estoque, registrar_movimento, resumo_estoque

router = APIRouter(tags=["estoque"])


@router.get("/fazendas/{fazenda_id}/estoque", response_model=ResumoEstoque)
def resumo(
    fazenda_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
) -> ResumoEstoque:
    faz = get_fazenda_no_escopo(fazenda_id, db, user)
    r = resumo_estoque(db, faz)
    return ResumoEstoque(
        saldo_t=r["saldo_t"], consumo_diario_t=r["consumo_diario_t"], dias=r["dias"],
        movimentos=[MovimentoOut.model_validate(m) for m in r["movimentos"]],
    )


@router.post("/fazendas/{fazenda_id}/estoque/movimentos", response_model=MovimentoOut, status_code=201)
def novo_movimento(
    fazenda_id: uuid.UUID,
    body: MovimentoIn,
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
) -> MovimentoVolumoso:
    faz = get_fazenda_no_escopo(fazenda_id, db, user)
    if body.tipo not in ("entrada", "saida"):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "tipo deve ser 'entrada' ou 'saida'")
    m = registrar_movimento(db, faz.id, body.data or date.today(), body.tipo, body.quantidade_t, body.descricao)
    db.commit()
    recomputar_estoque(db, faz)
    db.refresh(m)
    return m


@router.delete("/estoque/movimentos/{mov_id}", status_code=204)
def excluir_movimento(
    mov_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
) -> None:
    m = db.get(MovimentoVolumoso, mov_id)
    if m is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Movimento não encontrado")
    faz = get_fazenda_no_escopo(m.fazenda_id, db, user)
    db.delete(m)
    db.commit()
    recomputar_estoque(db, faz)
