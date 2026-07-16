import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import get_current_user, get_fazenda_no_escopo
from app.models.mercado import CotacaoArroba, CotacaoInsumo
from app.models.usuario import Usuario
from app.schemas import (
    BuscaArroba,
    CotacaoArrobaIn,
    CotacaoArrobaOut,
    CotacaoInsumoIn,
    CotacaoInsumoOut,
    ResumoMercado,
)
from app.services.mercado import (
    buscar_cotacao_arroba,
    custo_kg_ms,
    registrar_cotacao_arroba,
    resumo_mercado,
)

router = APIRouter(tags=["mercado"])


def _insumo_out(cot: CotacaoInsumo) -> CotacaoInsumoOut:
    entregue, kg_ms = custo_kg_ms(cot)
    return CotacaoInsumoOut(
        id=cot.id, data=cot.data, insumo=cot.insumo, praca=cot.praca, unidade=cot.unidade,
        preco_origem=float(cot.preco_origem), frete=float(cot.frete), outros=float(cot.outros),
        ms_pct=float(cot.ms_pct), custo_entregue_kg=entregue, custo_kg_ms=kg_ms,
    )


@router.get("/fazendas/{fazenda_id}/mercado", response_model=ResumoMercado)
def resumo(
    fazenda_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
) -> ResumoMercado:
    faz = get_fazenda_no_escopo(fazenda_id, db, user)
    r = resumo_mercado(db, faz)
    return ResumoMercado(
        arroba_atual=r["arroba_atual"], arroba_data=r["arroba_data"],
        historico=[CotacaoArrobaOut.model_validate(a) for a in r["historico"]],
        insumos=[_insumo_out(i) for i in r["insumos"]],
    )


@router.post("/fazendas/{fazenda_id}/mercado/arroba", response_model=CotacaoArrobaOut, status_code=201)
def nova_arroba(
    fazenda_id: uuid.UUID,
    body: CotacaoArrobaIn,
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
) -> CotacaoArroba:
    faz = get_fazenda_no_escopo(fazenda_id, db, user)
    return registrar_cotacao_arroba(db, faz, body.data or date.today(), body.valor)


@router.post("/fazendas/{fazenda_id}/mercado/arroba/buscar", response_model=BuscaArroba)
def buscar_arroba(
    fazenda_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
) -> BuscaArroba:
    """Best-effort: tenta buscar a arroba numa fonte pública e registra se achar."""
    faz = get_fazenda_no_escopo(fazenda_id, db, user)
    resultado = buscar_cotacao_arroba()
    if resultado is None:
        return BuscaArroba(encontrado=False)
    valor, fonte = resultado
    registrar_cotacao_arroba(db, faz, date.today(), valor, origem="integracao", fonte=fonte)
    return BuscaArroba(encontrado=True, valor=valor, fonte=fonte)


@router.delete("/mercado/arroba/{cot_id}", status_code=204)
def excluir_arroba(
    cot_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
) -> None:
    cot = db.get(CotacaoArroba, cot_id)
    if cot is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Cotação não encontrada")
    get_fazenda_no_escopo(cot.fazenda_id, db, user)
    db.delete(cot)
    db.commit()


@router.post("/fazendas/{fazenda_id}/mercado/insumos", response_model=CotacaoInsumoOut, status_code=201)
def novo_insumo(
    fazenda_id: uuid.UUID,
    body: CotacaoInsumoIn,
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
) -> CotacaoInsumoOut:
    faz = get_fazenda_no_escopo(fazenda_id, db, user)
    cot = CotacaoInsumo(
        fazenda_id=faz.id, data=body.data or date.today(), insumo=body.insumo,
        praca=body.praca, unidade=body.unidade, preco_origem=body.preco_origem,
        frete=body.frete, outros=body.outros, ms_pct=body.ms_pct,
    )
    db.add(cot)
    db.commit()
    db.refresh(cot)
    return _insumo_out(cot)


@router.delete("/mercado/insumos/{cot_id}", status_code=204)
def excluir_insumo(
    cot_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
) -> None:
    cot = db.get(CotacaoInsumo, cot_id)
    if cot is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Cotação não encontrada")
    get_fazenda_no_escopo(cot.fazenda_id, db, user)
    db.delete(cot)
    db.commit()
