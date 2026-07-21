"""Nutrição: dieta por lote (itens: inclusão/preço/MS) -> custo/cab/dia e
consumo de MS (% do peso vivo) -> indicadores custo_dieta_cab_dia e consumo_ms_pv.
"""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.nutricao import Dieta
from app.models.organizacao import Fazenda
from app.models.rebanho import Animal, Lote, Pesagem
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


def _cabecas_do_lote(db: Session, lote_id) -> int:
    if lote_id is None:
        return 0
    return int(db.execute(
        select(func.count(Animal.id)).where(
            Animal.lote_id == lote_id, Animal.status == "ativo"
        )
    ).scalar_one() or 0)


def resumo_dietas(db: Session, fazenda: Fazenda) -> dict:
    """Quadro comparativo das dietas da fazenda (audio 2 do cliente).

    "eu tenho tres dietas hoje... a gente lanca o custo de cada dieta e a gente
    faz o custo medio". O custo medio ponderado usa as cabecas de cada lote —
    uma dieta cara num lote de 20 animais pesa menos que uma barata em 300.
    """
    dietas = list(db.execute(
        select(Dieta).where(Dieta.fazenda_id == fazenda.id, Dieta.ativa.is_(True))
        .order_by(Dieta.data.desc())
    ).scalars())

    linhas: list[dict] = []
    for d in dietas:
        calc = calcular_dieta(db, d)
        cabecas = _cabecas_do_lote(db, d.lote_id)
        custo = calc["custo_cab_dia"]
        # custo de cada insumo dentro da dieta — o "quanto cada ingrediente pesa"
        insumos = [
            {
                "ingrediente": i.ingrediente,
                "inclusao_kg": round(float(i.inclusao_kg), 3),
                "preco_kg": round(float(i.preco_kg), 4),
                "custo_cab_dia": round(float(i.inclusao_kg) * float(i.preco_kg), 2),
                "pct_custo": round(
                    float(i.inclusao_kg) * float(i.preco_kg) / custo, 4
                ) if custo else None,
            }
            for i in d.itens
        ]
        insumos.sort(key=lambda x: x["custo_cab_dia"], reverse=True)
        linhas.append({
            "id": d.id,
            "nome": d.nome,
            "lote_nome": (db.get(Lote, d.lote_id).nome if d.lote_id else None),
            "cabecas": cabecas,
            "custo_cab_dia": custo,
            "custo_dia_lote": round(custo * cabecas, 2) if cabecas else None,
            "kg_ms": calc["kg_ms"],
            "consumo_ms_pv": calc["consumo_ms_pv"],
            "insumos": insumos,
        })

    custos = [l["custo_cab_dia"] for l in linhas]
    total_cab = sum(l["cabecas"] for l in linhas)
    custo_total_dia = sum(
        l["custo_cab_dia"] * l["cabecas"] for l in linhas if l["cabecas"]
    )

    return {
        "total_dietas": len(linhas),
        "cabecas_atendidas": total_cab,
        "custo_medio": round(sum(custos) / len(custos), 2) if custos else None,
        "custo_medio_ponderado": round(custo_total_dia / total_cab, 2) if total_cab else None,
        "custo_total_dia": round(custo_total_dia, 2) if custo_total_dia else None,
        "mais_cara": max(linhas, key=lambda l: l["custo_cab_dia"])["nome"] if linhas else None,
        "mais_barata": min(linhas, key=lambda l: l["custo_cab_dia"])["nome"] if linhas else None,
        "dietas": linhas,
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
