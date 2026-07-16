"""Nutrição: dieta por lote (itens: inclusão/preço/MS) -> custo/cab/dia e
consumo de MS (% do peso vivo) -> indicadores custo_dieta_cab_dia e consumo_ms_pv.
"""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.nutricao import Dieta
from app.models.organizacao import Fazenda
from app.models.rebanho import Animal, Pesagem
from app.services.gatilhos import sincronizar_alertas
from app.services.indicador_util import upsert_indicador


def _peso_medio_lote(db: Session, lote_id) -> float | None:
    """Média do último peso de cada animal do lote."""
    if lote_id is None:
        return None
    ult = (
        select(Pesagem.animal_id, func.max(Pesagem.data).label("dmax"))
        .join(Animal, Animal.id == Pesagem.animal_id)
        .where(Animal.lote_id == lote_id)
        .group_by(Pesagem.animal_id)
        .subquery()
    )
    media = db.execute(
        select(func.avg(Pesagem.peso)).join(
            ult, (Pesagem.animal_id == ult.c.animal_id) & (Pesagem.data == ult.c.dmax)
        )
    ).scalar_one_or_none()
    return float(media) if media is not None else None


def calcular_dieta(db: Session, dieta: Dieta) -> dict:
    """custo/cab/dia, kg de MS e consumo de MS (% PV) de uma dieta."""
    custo = sum(float(i.inclusao_kg) * float(i.preco_kg) for i in dieta.itens)
    kg_ms = sum(float(i.inclusao_kg) * float(i.ms_pct) for i in dieta.itens)
    kg_mn = sum(float(i.inclusao_kg) for i in dieta.itens)
    peso = _peso_medio_lote(db, dieta.lote_id)
    consumo_ms_pv = round(kg_ms / peso, 4) if peso and peso > 0 else None
    return {
        "custo_cab_dia": round(custo, 2),
        "kg_ms": round(kg_ms, 3),
        "kg_mn": round(kg_mn, 3),
        "peso_medio_lote": round(peso, 1) if peso else None,
        "consumo_ms_pv": consumo_ms_pv,
    }


def recomputar_indicadores_dieta(db: Session, fazenda: Fazenda) -> dict | None:
    """Usa a dieta ativa mais recente da fazenda para alimentar os indicadores."""
    dieta = db.execute(
        select(Dieta)
        .where(Dieta.fazenda_id == fazenda.id, Dieta.ativa.is_(True))
        .order_by(Dieta.data.desc())
        .limit(1)
    ).scalar_one_or_none()
    if dieta is None:
        db.commit()
        return None
    calc = calcular_dieta(db, dieta)
    upsert_indicador(db, fazenda.id, "custo_dieta_cab_dia", calc["custo_cab_dia"])
    if calc["consumo_ms_pv"] is not None:
        upsert_indicador(db, fazenda.id, "consumo_ms_pv", calc["consumo_ms_pv"])
    db.commit()
    sincronizar_alertas(db, fazenda)
    return calc
