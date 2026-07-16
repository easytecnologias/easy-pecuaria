"""Sanitário: registrar aplicações (vacina/vermífugo/tratamento) num animal ou
lote inteiro; agenda de próximas aplicações e vencendo.
"""

from __future__ import annotations

from datetime import date, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.rebanho import Animal
from app.models.sanitario import EventoSanitario

VENCE_EM_DIAS = 15


def registrar_aplicacao(
    db: Session, fazenda_id, animal_ids: list, lote_id, tipo: str, produto: str,
    data_ref: date, proxima: date | None, dose: str | None, obs: str | None,
) -> int:
    for aid in animal_ids:
        db.add(EventoSanitario(
            fazenda_id=fazenda_id, animal_id=aid, lote_id=lote_id, tipo=tipo,
            produto=produto, data=data_ref, proxima_aplicacao=proxima, dose=dose, observacao=obs,
        ))
    db.commit()
    return len(animal_ids)


def resumo_sanitario(db: Session, fazenda) -> dict:
    hoje = date.today()
    limite = hoje + timedelta(days=VENCE_EM_DIAS)

    # agenda: agrupa próximas aplicações por produto + data (quantos animais)
    agenda = db.execute(
        select(
            EventoSanitario.produto, EventoSanitario.tipo,
            EventoSanitario.proxima_aplicacao, func.count(EventoSanitario.id)
        )
        .where(
            EventoSanitario.fazenda_id == fazenda.id,
            EventoSanitario.proxima_aplicacao.isnot(None),
            EventoSanitario.proxima_aplicacao >= hoje - timedelta(days=30),
        )
        .group_by(EventoSanitario.produto, EventoSanitario.tipo, EventoSanitario.proxima_aplicacao)
        .order_by(EventoSanitario.proxima_aplicacao)
    ).all()

    total = db.execute(
        select(func.count(EventoSanitario.id)).where(EventoSanitario.fazenda_id == fazenda.id)
    ).scalar_one()
    vencendo = sum(1 for _, _, prox, _ in agenda if prox and prox <= limite)

    # histórico recente (com brinco)
    hist = db.execute(
        select(EventoSanitario, Animal.brinco)
        .join(Animal, Animal.id == EventoSanitario.animal_id)
        .where(EventoSanitario.fazenda_id == fazenda.id)
        .order_by(EventoSanitario.data.desc())
        .limit(40)
    ).all()

    return {
        "total": total,
        "vencendo": vencendo,
        "agenda": [
            {"produto": p, "tipo": t, "proxima": prox, "animais": n, "vencido": prox < hoje,
             "vence_proximo": prox <= limite}
            for p, t, prox, n in agenda
        ],
        "historico": [
            {"id": e.id, "brinco": brinco, "tipo": e.tipo, "produto": e.produto,
             "data": e.data, "proxima": e.proxima_aplicacao, "dose": e.dose}
            for e, brinco in hist
        ],
    }


def eventos_do_animal(db: Session, animal_id) -> list[EventoSanitario]:
    return list(db.execute(
        select(EventoSanitario).where(EventoSanitario.animal_id == animal_id)
        .order_by(EventoSanitario.data.desc())
    ).scalars().all())
