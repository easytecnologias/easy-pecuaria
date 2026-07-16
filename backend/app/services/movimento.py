"""Movimentação de animais: compra/venda/morte/descarte/transferência.
Muda o status/lote do animal e alimenta os KPIs de rebanho (vendas/mortes,
composição), além de recalcular ocupação/GMD.
"""

from __future__ import annotations

from datetime import date, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.movimento import MovimentoAnimal
from app.models.organizacao import Fazenda
from app.models.rebanho import Animal
from app.services.rebanho import recomputar_indicadores_rebanho

# tipo -> novo status do animal (transferencia nao muda status)
STATUS_POR_TIPO = {
    "compra": "ativo",
    "venda": "vendido",
    "morte": "morto",
    "descarte": "descartado",
}


def registrar_movimento(
    db: Session, animal: Animal, tipo: str, data_ref: date, valor: float | None,
    motivo: str | None, lote_destino_id, obs: str | None,
) -> MovimentoAnimal:
    m = MovimentoAnimal(
        fazenda_id=animal.fazenda_id, animal_id=animal.id, tipo=tipo, data=data_ref,
        valor=valor, motivo=motivo, lote_destino_id=lote_destino_id, observacao=obs,
    )
    db.add(m)
    if tipo in STATUS_POR_TIPO:
        animal.status = STATUS_POR_TIPO[tipo]
    if tipo == "transferencia" and lote_destino_id:
        animal.lote_id = lote_destino_id
    db.commit()
    return m


def resumo_movimentos(db: Session, fazenda: Fazenda) -> dict:
    hoje = date.today()
    d30 = hoje - timedelta(days=30)

    def conta(tipo, desde=None):
        stmt = select(func.count(MovimentoAnimal.id)).where(
            MovimentoAnimal.fazenda_id == fazenda.id, MovimentoAnimal.tipo == tipo
        )
        if desde:
            stmt = stmt.where(MovimentoAnimal.data >= desde)
        return db.execute(stmt).scalar_one()

    movimentos = db.execute(
        select(MovimentoAnimal, Animal.brinco)
        .join(Animal, Animal.id == MovimentoAnimal.animal_id)
        .where(MovimentoAnimal.fazenda_id == fazenda.id)
        .order_by(MovimentoAnimal.data.desc())
        .limit(60)
    ).all()

    return {
        "vendas_30d": conta("venda", d30),
        "mortes_30d": conta("morte", d30),
        "descartes_30d": conta("descarte", d30),
        "compras_30d": conta("compra", d30),
        "movimentos": [
            {"id": m.id, "brinco": brinco, "tipo": m.tipo, "data": m.data,
             "valor": float(m.valor) if m.valor is not None else None, "motivo": m.motivo}
            for m, brinco in movimentos
        ],
    }


def composicao_rebanho(db: Session, fazenda: Fazenda) -> dict:
    """Distribuição do rebanho ativo por categoria + totais por sexo."""
    linhas = db.execute(
        select(Animal.categoria, func.count(Animal.id))
        .where(Animal.fazenda_id == fazenda.id, Animal.status == "ativo")
        .group_by(Animal.categoria)
    ).all()
    por_categoria = [{"categoria": c or "—", "total": n} for c, n in linhas]

    def sexo(s):
        return db.execute(
            select(func.count(Animal.id)).where(
                Animal.fazenda_id == fazenda.id, Animal.status == "ativo", Animal.sexo == s
            )
        ).scalar_one()

    total = sum(n for _, n in linhas)
    return {"total": total, "femeas": sexo("F"), "machos": sexo("M"),
            "por_categoria": sorted(por_categoria, key=lambda x: -x["total"])}


def movimentos_do_animal(db: Session, animal_id) -> list[MovimentoAnimal]:
    return list(db.execute(
        select(MovimentoAnimal).where(MovimentoAnimal.animal_id == animal_id)
        .order_by(MovimentoAnimal.data.desc())
    ).scalars().all())
