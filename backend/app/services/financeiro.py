"""Financeiro: lançamentos (despesa/receita) -> saldo, margem por cabeça e
capital de giro (dias) -> indicadores margem_cab / capital_giro_dias -> gatilhos.
"""

from __future__ import annotations

from datetime import date, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.financeiro import LancamentoFinanceiro
from app.models.organizacao import Fazenda
from app.models.rebanho import Animal
from app.services.gatilhos import sincronizar_alertas
from app.services.indicador_util import upsert_indicador

TIPOS = ("despesa", "receita")


def registrar_lancamento(
    db: Session, fazenda_id, data_ref: date, tipo: str, categoria: str,
    valor: float, descricao: str | None,
) -> LancamentoFinanceiro:
    lanc = LancamentoFinanceiro(
        fazenda_id=fazenda_id, data=data_ref, tipo=tipo,
        categoria=categoria, valor=valor, descricao=descricao,
    )
    db.add(lanc)
    db.flush()
    return lanc


def _totais(db: Session, fazenda_id) -> dict:
    def soma(tipo, desde=None):
        stmt = select(func.coalesce(func.sum(LancamentoFinanceiro.valor), 0)).where(
            LancamentoFinanceiro.fazenda_id == fazenda_id,
            LancamentoFinanceiro.tipo == tipo,
        )
        if desde is not None:
            stmt = stmt.where(LancamentoFinanceiro.data >= desde)
        return float(db.execute(stmt).scalar_one())

    receitas = soma("receita")
    despesas = soma("despesa")
    saldo = receitas - despesas

    n_animais = int(db.execute(
        select(func.count(Animal.id)).where(
            Animal.fazenda_id == fazenda_id, Animal.status == "ativo"
        )
    ).scalar_one())

    # margem por cabeça = resultado líquido / rebanho ativo
    margem_cab = round(saldo / n_animais, 2) if n_animais > 0 else None

    # capital de giro em dias = caixa / despesa média diária (últimos 90 dias)
    despesas90 = soma("despesa", date.today() - timedelta(days=90))
    desp_diaria = despesas90 / 90 if despesas90 > 0 else None
    if desp_diaria and desp_diaria > 0:
        capital_giro_dias = round(max(saldo, 0) / desp_diaria)
    else:
        capital_giro_dias = None

    return {
        "receitas": round(receitas, 2), "despesas": round(despesas, 2),
        "saldo": round(saldo, 2), "n_animais": n_animais,
        "margem_cab": margem_cab, "capital_giro_dias": capital_giro_dias,
    }


def recomputar_financeiro(db: Session, fazenda: Fazenda) -> dict:
    t = _totais(db, fazenda.id)
    if t["margem_cab"] is not None:
        upsert_indicador(db, fazenda.id, "margem_cab", t["margem_cab"])
    if t["capital_giro_dias"] is not None:
        upsert_indicador(db, fazenda.id, "capital_giro_dias", t["capital_giro_dias"])
    db.commit()
    sincronizar_alertas(db, fazenda)
    return t


def resumo_financeiro(db: Session, fazenda: Fazenda) -> dict:
    t = _totais(db, fazenda.id)
    # quebra por categoria (para o gráfico de despesas/receitas)
    por_cat = db.execute(
        select(
            LancamentoFinanceiro.tipo, LancamentoFinanceiro.categoria,
            func.coalesce(func.sum(LancamentoFinanceiro.valor), 0),
        )
        .where(LancamentoFinanceiro.fazenda_id == fazenda.id)
        .group_by(LancamentoFinanceiro.tipo, LancamentoFinanceiro.categoria)
        .order_by(func.sum(LancamentoFinanceiro.valor).desc())
    ).all()
    categorias = [
        {"tipo": tp, "categoria": cat, "total": round(float(tot), 2)}
        for tp, cat, tot in por_cat
    ]
    lancamentos = db.execute(
        select(LancamentoFinanceiro)
        .where(LancamentoFinanceiro.fazenda_id == fazenda.id)
        .order_by(LancamentoFinanceiro.data.desc())
        .limit(200)
    ).scalars().all()
    return {**t, "categorias": categorias, "lancamentos": lancamentos}
