"""Silagem como modulo proprio (audio 8 do cliente).

"silagem ela tem que ficar a parte, e uma parte propria, porque vai ter varios
tipos de silagem" — cada silo tem tipo, meta de materia seca, umidade,
temperatura, e os dados da colheita (maquinario, destino).

O estoque de volumoso (dias de silagem) continua no modulo Estoque; aqui e a
QUALIDADE e a composicao por tipo de silo.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.organizacao import Fazenda
from app.models.parametro import Parametro
from app.models.silagem import Silagem


def _ms_alvo(db: Session, fazenda: Fazenda) -> float | None:
    p = db.execute(
        select(Parametro).where(
            Parametro.fazenda_id == fazenda.id, Parametro.chave == "ms_alvo_ensilagem"
        )
    ).scalar_one_or_none()
    return float(p.valor) if p else None


def listar(db: Session, fazenda: Fazenda) -> list[Silagem]:
    return list(db.execute(
        select(Silagem).where(Silagem.fazenda_id == fazenda.id)
        .order_by(Silagem.data_ensilagem.desc().nullslast(), Silagem.nome)
    ).scalars())


def resumo(db: Session, fazenda: Fazenda) -> dict:
    silos = listar(db, fazenda)
    abertos = [s for s in silos if s.situacao != "consumido"]

    total_t = sum(float(s.quantidade_t) for s in silos if s.quantidade_t)
    consumo = sum(float(s.consumo_diario_t) for s in abertos if s.consumo_diario_t)

    com_ms = [s for s in silos if s.ms_real is not None]
    ms_media = round(sum(float(s.ms_real) for s in com_ms) / len(com_ms), 4) if com_ms else None

    por_tipo: dict[str, float] = {}
    for s in silos:
        if s.quantidade_t:
            por_tipo[s.tipo] = round(por_tipo.get(s.tipo, 0) + float(s.quantidade_t), 3)

    # silos fora do alvo de materia seca — o que exige acao
    alvo = _ms_alvo(db, fazenda)
    fora_do_alvo = [
        s.nome for s in com_ms
        if alvo is not None and abs(float(s.ms_real) - alvo) > 0.03
    ]

    # audio 3: estoque de seguranca — o silo que ja chegou no minimo definido
    abaixo_seguranca = [
        s.nome for s in abertos
        if s.estoque_seguranca_t is not None and s.quantidade_t is not None
        and float(s.quantidade_t) <= float(s.estoque_seguranca_t)
    ]
    seguranca_t = sum(
        float(s.estoque_seguranca_t) for s in abertos if s.estoque_seguranca_t
    )
    # quantos dias ate o estoque total encostar na reserva de seguranca — e o
    # prazo que sobra para plantar/colher de novo sem ficar sem volumoso
    dias_ate_seguranca = (
        int((total_t - seguranca_t) / consumo) if consumo and total_t > seguranca_t else None
    )

    return {
        "total_silos": len(silos),
        "silos_abertos": len(abertos),
        "total_t": round(total_t, 3),
        "consumo_diario_t": round(consumo, 3) if consumo else None,
        "dias_estimados": int(total_t / consumo) if consumo else None,
        "ms_media": ms_media,
        "ms_alvo": alvo,
        "fora_do_alvo": fora_do_alvo,
        "abaixo_seguranca": abaixo_seguranca,
        "estoque_seguranca_t": round(seguranca_t, 3) if seguranca_t else None,
        "dias_ate_seguranca": dias_ate_seguranca,
        "por_tipo": por_tipo,
        "silos": silos,
    }
