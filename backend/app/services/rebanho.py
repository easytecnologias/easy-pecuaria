"""Regras do rebanho: calcular GMD de uma pesagem e traduzir os eventos do rebanho
em indicadores da fazenda (que alimentam o painel e os gatilhos).
"""

from __future__ import annotations

from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.indicador import IndicadorDefinicao, IndicadorValor
from app.models.organizacao import Fazenda
from app.models.parametro import Parametro
from app.models.rebanho import Animal, Lote, Pesagem
from app.services.gatilhos import sincronizar_alertas

# categorias de lote consideradas confinamento/engorda
CATEGORIAS_CONFINAMENTO = ("Engorda", "Confinamento")


def registrar_pesagem(
    db: Session, animal: Animal, data_ref: date, peso: float, observacao: str | None = None
) -> Pesagem:
    """Cria a pesagem calculando o GMD contra a pesagem anterior do animal."""
    anterior = db.execute(
        select(Pesagem)
        .where(Pesagem.animal_id == animal.id, Pesagem.data < data_ref)
        .order_by(Pesagem.data.desc())
        .limit(1)
    ).scalar_one_or_none()

    gmd = None
    if anterior is not None:
        dias = (data_ref - anterior.data).days
        if dias > 0:
            gmd = round((peso - float(anterior.peso)) / dias, 3)

    # uma pesagem por animal por dia: se ja existe na data, atualiza
    pesagem = db.execute(
        select(Pesagem).where(Pesagem.animal_id == animal.id, Pesagem.data == data_ref)
    ).scalar_one_or_none()
    if pesagem is not None:
        pesagem.peso = peso
        pesagem.gmd = gmd
        pesagem.observacao = observacao
    else:
        pesagem = Pesagem(
            fazenda_id=animal.fazenda_id,
            animal_id=animal.id,
            data=data_ref,
            peso=peso,
            gmd=gmd,
            observacao=observacao,
        )
        db.add(pesagem)
    db.flush()
    return pesagem


def _upsert_indicador(db: Session, fazenda_id, codigo: str, valor: float, quando: date) -> None:
    indicador = db.execute(
        select(IndicadorDefinicao).where(IndicadorDefinicao.codigo == codigo)
    ).scalar_one_or_none()
    if indicador is None:
        return
    existente = db.execute(
        select(IndicadorValor).where(
            IndicadorValor.fazenda_id == fazenda_id,
            IndicadorValor.indicador_id == indicador.id,
            IndicadorValor.data_ref == quando,
        )
    ).scalar_one_or_none()
    if existente:
        existente.valor = valor
    else:
        db.add(IndicadorValor(
            fazenda_id=fazenda_id, indicador_id=indicador.id,
            valor=valor, data_ref=quando, origem="calculo",
        ))


def recomputar_indicadores_rebanho(db: Session, fazenda: Fazenda) -> dict:
    """Recalcula, a partir dos eventos do rebanho:
      - gmd: media do ultimo GMD por animal em lotes de confinamento
      - ocupacao_confinamento: animais em confinamento / capacidade (parametro)
    Depois reavalia os gatilhos. Retorna os valores calculados.
    """
    hoje = date.today()

    # ultimo GMD de cada animal (subquery da pesagem mais recente com gmd)
    ult = (
        select(Pesagem.animal_id, func.max(Pesagem.data).label("dmax"))
        .where(Pesagem.fazenda_id == fazenda.id, Pesagem.gmd.isnot(None))
        .group_by(Pesagem.animal_id)
        .subquery()
    )
    gmds = db.execute(
        select(Pesagem.gmd)
        .join(ult, (Pesagem.animal_id == ult.c.animal_id) & (Pesagem.data == ult.c.dmax))
        .join(Animal, Animal.id == Pesagem.animal_id)
        .join(Lote, Lote.id == Animal.lote_id)
        .where(Lote.categoria.in_(CATEGORIAS_CONFINAMENTO))
    ).scalars().all()
    valores_gmd = [float(g) for g in gmds if g is not None]
    gmd_medio = round(sum(valores_gmd) / len(valores_gmd), 3) if valores_gmd else None

    # ocupacao = animais ativos em lotes de confinamento / capacidade
    n_confinamento = db.execute(
        select(func.count(Animal.id))
        .join(Lote, Lote.id == Animal.lote_id)
        .where(
            Animal.fazenda_id == fazenda.id,
            Animal.status == "ativo",
            Lote.categoria.in_(CATEGORIAS_CONFINAMENTO),
        )
    ).scalar_one()
    capacidade = db.execute(
        select(Parametro.valor).where(
            Parametro.fazenda_id == fazenda.id,
            Parametro.chave == "capacidade_confinamento",
        )
    ).scalar_one_or_none()
    ocupacao = (
        round(n_confinamento / float(capacidade), 4)
        if capacidade and float(capacidade) > 0
        else None
    )

    if gmd_medio is not None:
        _upsert_indicador(db, fazenda.id, "gmd", gmd_medio, hoje)
    if ocupacao is not None:
        _upsert_indicador(db, fazenda.id, "ocupacao_confinamento", ocupacao, hoje)

    db.commit()
    sincronizar_alertas(db, fazenda)
    return {"gmd": gmd_medio, "ocupacao_confinamento": ocupacao, "n_confinamento": n_confinamento}
