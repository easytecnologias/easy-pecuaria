"""Reprodução: registrar inseminação/DG e transformar em taxa de prenhez
(indicador da fazenda que alimenta o gatilho) + análise por touro/inseminador.
"""

from __future__ import annotations

from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.indicador import IndicadorDefinicao, IndicadorValor
from app.models.organizacao import Fazenda
from app.models.reproducao import Inseminacao
from app.services.gatilhos import sincronizar_alertas


def registrar_inseminacao(
    db: Session, animal_id, fazenda_id, data_ref: date, touro: str,
    inseminador: str | None, protocolo: str | None,
) -> Inseminacao:
    ins = Inseminacao(
        fazenda_id=fazenda_id, animal_id=animal_id, data=data_ref,
        touro=touro, inseminador=inseminador, protocolo=protocolo, resultado="pendente",
    )
    db.add(ins)
    db.flush()
    return ins


def registrar_dg(db: Session, ins: Inseminacao, resultado: str, dg_data: date | None) -> None:
    ins.resultado = resultado  # prenhe | vazia
    ins.dg_data = dg_data or date.today()
    db.flush()


def recomputar_taxa_prenhez(db: Session, fazenda: Fazenda) -> float | None:
    """taxa = prenhes / (prenhes + vazias) entre as inseminações já diagnosticadas."""
    prenhes = db.execute(
        select(func.count(Inseminacao.id)).where(
            Inseminacao.fazenda_id == fazenda.id, Inseminacao.resultado == "prenhe"
        )
    ).scalar_one()
    vazias = db.execute(
        select(func.count(Inseminacao.id)).where(
            Inseminacao.fazenda_id == fazenda.id, Inseminacao.resultado == "vazia"
        )
    ).scalar_one()
    diagnosticadas = prenhes + vazias
    if diagnosticadas == 0:
        db.commit()
        return None
    taxa = round(prenhes / diagnosticadas, 4)

    indicador = db.execute(
        select(IndicadorDefinicao).where(IndicadorDefinicao.codigo == "taxa_prenhez")
    ).scalar_one_or_none()
    if indicador is not None:
        hoje = date.today()
        existente = db.execute(
            select(IndicadorValor).where(
                IndicadorValor.fazenda_id == fazenda.id,
                IndicadorValor.indicador_id == indicador.id,
                IndicadorValor.data_ref == hoje,
            )
        ).scalar_one_or_none()
        if existente:
            existente.valor = taxa
        else:
            db.add(IndicadorValor(
                fazenda_id=fazenda.id, indicador_id=indicador.id,
                valor=taxa, data_ref=hoje, origem="calculo",
            ))
    db.commit()
    sincronizar_alertas(db, fazenda)
    return taxa


def resumo_reproducao(db: Session, fazenda: Fazenda) -> dict:
    ins = db.execute(
        select(Inseminacao).where(Inseminacao.fazenda_id == fazenda.id)
    ).scalars().all()

    total = len(ins)
    prenhes = sum(1 for i in ins if i.resultado == "prenhe")
    vazias = sum(1 for i in ins if i.resultado == "vazia")
    pendentes = sum(1 for i in ins if i.resultado == "pendente")
    diagnosticadas = prenhes + vazias
    taxa = round(prenhes / diagnosticadas, 4) if diagnosticadas else None

    def agrupar(chave: str) -> list[dict]:
        grupos: dict[str, dict] = {}
        for i in ins:
            k = (getattr(i, chave) or "—")
            g = grupos.setdefault(k, {"nome": k, "total": 0, "prenhes": 0, "vazias": 0})
            g["total"] += 1
            if i.resultado == "prenhe":
                g["prenhes"] += 1
            elif i.resultado == "vazia":
                g["vazias"] += 1
        for g in grupos.values():
            diag = g["prenhes"] + g["vazias"]
            g["taxa"] = round(g["prenhes"] / diag, 4) if diag else None
        return sorted(grupos.values(), key=lambda x: (x["taxa"] is None, -(x["taxa"] or 0)))

    return {
        "total": total, "prenhes": prenhes, "vazias": vazias, "pendentes": pendentes,
        "taxa_prenhez": taxa,
        "por_touro": agrupar("touro"),
        "por_inseminador": agrupar("inseminador"),
    }
