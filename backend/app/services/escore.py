"""Escore de condição corporal (ECC): avaliações por animal, escala 1–5.
O último escore de cada animal vira a distribuição magra/ideal/gorda da fazenda.
"""

from __future__ import annotations

from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.escore import EscoreCorporal
from app.models.organizacao import Fazenda
from app.models.rebanho import Animal

# faixas de referência (matriz de corte): abaixo de 2.5 magra, acima de 3.5 gorda
IDEAL_MIN = 2.5
IDEAL_MAX = 3.5


def registrar_escore(
    db: Session, fazenda_id, animal_id, data_ref: date, escore: float, obs: str | None
) -> EscoreCorporal:
    # um escore por animal por dia: se já existe na data, atualiza
    ecc = db.execute(
        select(EscoreCorporal).where(
            EscoreCorporal.animal_id == animal_id, EscoreCorporal.data == data_ref
        )
    ).scalar_one_or_none()
    if ecc is not None:
        ecc.escore = escore
        ecc.observacao = obs
    else:
        ecc = EscoreCorporal(
            fazenda_id=fazenda_id, animal_id=animal_id, data=data_ref,
            escore=escore, observacao=obs,
        )
        db.add(ecc)
    db.flush()
    return ecc


def resumo_escore(db: Session, fazenda: Fazenda) -> dict:
    # último escore de cada animal (avaliação mais recente)
    ult = (
        select(EscoreCorporal.animal_id, func.max(EscoreCorporal.data).label("dmax"))
        .where(EscoreCorporal.fazenda_id == fazenda.id)
        .group_by(EscoreCorporal.animal_id)
        .subquery()
    )
    ultimos = db.execute(
        select(EscoreCorporal.escore)
        .join(ult, (EscoreCorporal.animal_id == ult.c.animal_id) & (EscoreCorporal.data == ult.c.dmax))
    ).scalars().all()
    valores = [float(v) for v in ultimos]

    n = len(valores)
    magras = sum(1 for v in valores if v < IDEAL_MIN)
    gordas = sum(1 for v in valores if v > IDEAL_MAX)
    ideais = n - magras - gordas
    media = round(sum(valores) / n, 2) if n else None
    pct_ideais = round(ideais / n, 4) if n else None

    # histórico recente (avaliações), com brinco do animal
    historico = db.execute(
        select(EscoreCorporal, Animal.brinco, Animal.categoria)
        .join(Animal, Animal.id == EscoreCorporal.animal_id)
        .where(EscoreCorporal.fazenda_id == fazenda.id)
        .order_by(EscoreCorporal.data.desc())
        .limit(200)
    ).all()

    return {
        "n_avaliados": n, "media": media, "magras": magras, "ideais": ideais,
        "gordas": gordas, "pct_ideais": pct_ideais, "historico": historico,
    }
