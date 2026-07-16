"""Estoque de volumoso: movimentos (entrada/saída, toneladas) -> saldo e dias de
estoque -> indicador estoque_silagem_dias -> gatilho.
"""

from __future__ import annotations

from datetime import date, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.estoque import MovimentoVolumoso
from app.models.organizacao import Fazenda
from app.services.gatilhos import sincronizar_alertas
from app.services.indicador_util import upsert_indicador


def registrar_movimento(
    db: Session, fazenda_id, data_ref: date, tipo: str, quantidade_t: float, descricao: str | None
) -> MovimentoVolumoso:
    m = MovimentoVolumoso(
        fazenda_id=fazenda_id, data=data_ref, tipo=tipo,
        quantidade_t=quantidade_t, descricao=descricao,
    )
    db.add(m)
    db.flush()
    return m


def _saldo_e_consumo(db: Session, fazenda_id) -> tuple[float, float | None, float | None]:
    def soma(tipo, desde=None):
        stmt = select(func.coalesce(func.sum(MovimentoVolumoso.quantidade_t), 0)).where(
            MovimentoVolumoso.fazenda_id == fazenda_id, MovimentoVolumoso.tipo == tipo
        )
        if desde is not None:
            stmt = stmt.where(MovimentoVolumoso.data >= desde)
        return float(db.execute(stmt).scalar_one())

    saldo = soma("entrada") - soma("saida")
    saidas30 = soma("saida", date.today() - timedelta(days=30))
    consumo = round(saidas30 / 30, 3) if saidas30 > 0 else None
    dias = round(saldo / consumo, 1) if consumo and consumo > 0 else None
    return round(saldo, 3), consumo, dias


def recomputar_estoque(db: Session, fazenda: Fazenda) -> dict:
    saldo, consumo, dias = _saldo_e_consumo(db, fazenda.id)
    if dias is not None:
        upsert_indicador(db, fazenda.id, "estoque_silagem_dias", dias)
    db.commit()
    sincronizar_alertas(db, fazenda)
    return {"saldo_t": saldo, "consumo_diario_t": consumo, "dias": dias}


def resumo_estoque(db: Session, fazenda: Fazenda) -> dict:
    saldo, consumo, dias = _saldo_e_consumo(db, fazenda.id)
    movimentos = db.execute(
        select(MovimentoVolumoso)
        .where(MovimentoVolumoso.fazenda_id == fazenda.id)
        .order_by(MovimentoVolumoso.data.desc())
    ).scalars().all()
    return {"saldo_t": saldo, "consumo_diario_t": consumo, "dias": dias, "movimentos": movimentos}
