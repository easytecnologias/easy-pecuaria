import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import get_current_user, get_fazenda_no_escopo
from app.models.gatilho import RegraGatilho
from app.models.indicador import IndicadorDefinicao, IndicadorValor
from app.models.usuario import Usuario
from app.schemas import IndicadorOut, RegraOut, ValorIn
from app.services.gatilhos import sincronizar_alertas

router = APIRouter(tags=["indicadores"])


@router.get("/regras", response_model=list[RegraOut])
def listar_regras(
    db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)
) -> list[RegraOut]:
    """Regras de gatilho da organizacao — para mostrar a ligacao meta -> alerta."""
    linhas = db.execute(
        select(RegraGatilho, IndicadorDefinicao)
        .join(IndicadorDefinicao, IndicadorDefinicao.id == RegraGatilho.indicador_id)
        .where(RegraGatilho.org_id == user.org_id, RegraGatilho.ativo.is_(True))
    ).all()
    return [
        RegraOut(
            id=r.id, nome=r.nome, indicador_codigo=ind.codigo, indicador_nome=ind.nome,
            operador=r.operador.value, tipo_referencia=r.tipo_referencia.value,
            parametro_chave=r.parametro_chave,
            valor_referencia=float(r.valor_referencia) if r.valor_referencia is not None else None,
            tolerancia=float(r.tolerancia) if r.tolerancia is not None else None,
            severidade=r.severidade, acao=r.acao,
        )
        for r, ind in linhas
    ]


@router.get("/indicadores", response_model=list[IndicadorOut])
def catalogo_indicadores(
    db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)
) -> list[IndicadorOut]:
    return list(
        db.execute(select(IndicadorDefinicao).order_by(IndicadorDefinicao.categoria)).scalars().all()
    )


@router.post("/fazendas/{fazenda_id}/indicadores/valores", status_code=status.HTTP_201_CREATED)
def lancar_valor(
    fazenda_id: uuid.UUID,
    body: ValorIn,
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
) -> dict:
    """Lanca (ou atualiza) o valor de um indicador na fazenda e reavalia os gatilhos."""
    faz = get_fazenda_no_escopo(fazenda_id, db, user)
    indicador = db.execute(
        select(IndicadorDefinicao).where(IndicadorDefinicao.codigo == body.indicador_codigo)
    ).scalar_one_or_none()
    if indicador is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Indicador nao encontrado")

    data_ref = body.data_ref or date.today()
    existente = db.execute(
        select(IndicadorValor).where(
            IndicadorValor.fazenda_id == faz.id,
            IndicadorValor.indicador_id == indicador.id,
            IndicadorValor.data_ref == data_ref,
        )
    ).scalar_one_or_none()

    if existente:
        existente.valor = body.valor
        existente.observacao = body.observacao
    else:
        db.add(IndicadorValor(
            fazenda_id=faz.id, indicador_id=indicador.id,
            valor=body.valor, data_ref=data_ref, observacao=body.observacao,
        ))
    db.commit()

    # reavalia gatilhos apos o novo dado
    sincronizar_alertas(db, faz)
    return {"ok": True, "indicador": indicador.codigo, "valor": body.valor, "data_ref": str(data_ref)}


@router.get("/fazendas/{fazenda_id}/indicadores/{codigo}/serie")
def serie_indicador(
    fazenda_id: uuid.UUID,
    codigo: str,
    db: Session = Depends(get_db),
    user: Usuario = Depends(get_current_user),
) -> list[dict]:
    """Serie temporal de um indicador (para graficos de tendencia)."""
    faz = get_fazenda_no_escopo(fazenda_id, db, user)
    indicador = db.execute(
        select(IndicadorDefinicao).where(IndicadorDefinicao.codigo == codigo)
    ).scalar_one_or_none()
    if indicador is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Indicador nao encontrado")
    linhas = db.execute(
        select(IndicadorValor.data_ref, IndicadorValor.valor)
        .where(IndicadorValor.fazenda_id == faz.id, IndicadorValor.indicador_id == indicador.id)
        .order_by(IndicadorValor.data_ref)
    ).all()
    return [{"data_ref": str(d), "valor": float(v)} for d, v in linhas]
