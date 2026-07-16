import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import get_current_user, get_fazenda_no_escopo
from app.models.financeiro import LancamentoFinanceiro
from app.models.usuario import Usuario
from app.schemas import CategoriaFinanceira, LancamentoIn, LancamentoOut, ResumoFinanceiro
from app.services.financeiro import (
    TIPOS, recomputar_financeiro, registrar_lancamento, resumo_financeiro,
)

router = APIRouter(tags=["financeiro"])


@router.get("/fazendas/{fazenda_id}/financeiro", response_model=ResumoFinanceiro)
def resumo(
    fazenda_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
) -> ResumoFinanceiro:
    faz = get_fazenda_no_escopo(fazenda_id, db, user)
    r = resumo_financeiro(db, faz)
    return ResumoFinanceiro(
        receitas=r["receitas"], despesas=r["despesas"], saldo=r["saldo"],
        n_animais=r["n_animais"], margem_cab=r["margem_cab"],
        capital_giro_dias=r["capital_giro_dias"],
        categorias=[CategoriaFinanceira(**c) for c in r["categorias"]],
        lancamentos=[LancamentoOut.model_validate(x) for x in r["lancamentos"]],
    )


@router.post("/fazendas/{fazenda_id}/financeiro/lancamentos", response_model=LancamentoOut, status_code=201)
def novo_lancamento(
    fazenda_id: uuid.UUID,
    body: LancamentoIn,
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
) -> LancamentoFinanceiro:
    faz = get_fazenda_no_escopo(fazenda_id, db, user)
    if body.tipo not in TIPOS:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "tipo deve ser 'despesa' ou 'receita'")
    if not body.categoria.strip():
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "informe a categoria")
    if body.valor <= 0:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "valor deve ser positivo")
    lanc = registrar_lancamento(
        db, faz.id, body.data or date.today(), body.tipo,
        body.categoria.strip(), body.valor, body.descricao,
    )
    db.commit()
    recomputar_financeiro(db, faz)
    db.refresh(lanc)
    return lanc


@router.delete("/financeiro/lancamentos/{lanc_id}", status_code=204)
def excluir_lancamento(
    lanc_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
) -> None:
    lanc = db.get(LancamentoFinanceiro, lanc_id)
    if lanc is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Lançamento não encontrado")
    faz = get_fazenda_no_escopo(lanc.fazenda_id, db, user)
    db.delete(lanc)
    db.commit()
    recomputar_financeiro(db, faz)
