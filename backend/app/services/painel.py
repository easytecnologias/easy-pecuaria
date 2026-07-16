"""Monta os DTOs do painel a partir da avaliacao das regras (motor de gatilhos)."""

from __future__ import annotations

from collections import Counter
from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.enums import Severidade
from app.models.gatilho import RegraGatilho
from app.models.indicador import IndicadorDefinicao
from app.models.organizacao import Fazenda, Organizacao
from app.models.rebanho import Animal

MESES_PT = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]
from app.schemas import (
    DashboardOut,
    FazendaPainelOut,
    IndicadorPainelOut,
    ResumoDashboard,
)
from app.services.gatilhos import avaliar_fazenda


def montar_painel_fazenda(
    db: Session, fazenda: Fazenda, regras=None, indicadores=None
) -> FazendaPainelOut:
    resultados = avaliar_fazenda(db, fazenda, regras=regras, indicadores=indicadores)
    indicadores: list[IndicadorPainelOut] = []
    contagem: Counter[str] = Counter()

    for r in resultados:
        contagem[r.severidade.value] += 1
        ind = r.indicador
        indicadores.append(
            IndicadorPainelOut(
                codigo=ind.codigo,
                nome=ind.nome,
                categoria=ind.categoria,
                unidade=ind.unidade,
                formato=ind.formato,
                casas_decimais=ind.casas_decimais,
                valor=r.valor_observado,
                data_ref=r.data_valor,
                situacao=r.severidade,
                referencia=r.valor_referencia,
                acao=r.acao,
            )
        )

    alertas_abertos = sum(v for k, v in contagem.items() if k != Severidade.ok.value)
    por_sev = {k: v for k, v in contagem.items() if k != Severidade.ok.value}

    return FazendaPainelOut(
        id=fazenda.id,
        nome=fazenda.nome,
        municipio=fazenda.municipio,
        uf=fazenda.uf,
        alertas_abertos=alertas_abertos,
        por_severidade=por_sev,
        indicadores=indicadores,
    )


def montar_dashboard(
    db: Session, organizacao: Organizacao, fazendas: list[Fazenda]
) -> DashboardOut:
    # carrega regras + catalogo de indicadores uma vez, reusa nas 3 fazendas
    regras = list(
        db.execute(
            select(RegraGatilho).where(
                RegraGatilho.org_id == organizacao.id, RegraGatilho.ativo.is_(True)
            )
        ).scalars().all()
    )
    indicadores = {i.id: i for i in db.execute(select(IndicadorDefinicao)).scalars().all()}
    paineis = [montar_painel_fazenda(db, f, regras, indicadores) for f in fazendas]

    total_sev: Counter[str] = Counter()
    for p in paineis:
        for k, v in p.por_severidade.items():
            total_sev[k] += v
    alertas_abertos = sum(total_sev.values())

    return DashboardOut(
        organizacao=organizacao.nome,
        resumo=ResumoDashboard(
            fazendas=len(fazendas),
            alertas_abertos=alertas_abertos,
            por_severidade=dict(total_sev),
        ),
        fazendas=paineis,
    )


def evolucao_rebanho(db: Session, fazendas: list[Fazenda]) -> dict:
    """Evolução do rebanho: nascimentos por mês nos últimos 12 meses (grupo)."""
    ids = [f.id for f in fazendas]
    hoje = date.today()
    # sequência dos 12 meses terminando no mês atual
    seq = []
    yy, mm = hoje.year, hoje.month
    for _ in range(12):
        seq.append((yy, mm))
        mm -= 1
        if mm == 0:
            mm = 12
            yy -= 1
    seq.reverse()

    mapa: dict[str, int] = {}
    total_ativos = 0
    if ids:
        inicio = date(seq[0][0], seq[0][1], 1)
        datas = db.execute(
            select(Animal.data_nascimento).where(
                Animal.fazenda_id.in_(ids),
                Animal.data_nascimento.isnot(None),
                Animal.data_nascimento >= inicio,
            )
        ).scalars().all()
        for d in datas:
            chave = f"{d.year:04d}-{d.month:02d}"
            mapa[chave] = mapa.get(chave, 0) + 1
        total_ativos = int(db.execute(
            select(func.count(Animal.id)).where(
                Animal.fazenda_id.in_(ids), Animal.status == "ativo"
            )
        ).scalar_one())

    meses = [
        {"periodo": f"{a:04d}-{m:02d}", "label": MESES_PT[m - 1], "ano": str(a),
         "nascimentos": mapa.get(f"{a:04d}-{m:02d}", 0)}
        for a, m in seq
    ]
    return {
        "meses": meses,
        "total_nascimentos_12m": sum(x["nascimentos"] for x in meses),
        "total_ativos": total_ativos,
    }
