"""Desmame (audio 7 do cliente).

O cliente quer o peso medio de desmama POR BEZERRO (nao um numero solto), com
o vinculo matriz -> bezerro, e comparar com as metas de desmama/prenhez.
Alimenta o indicador peso_desmama_real para entrar no motor de gatilhos.
"""

from __future__ import annotations

from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.organizacao import Fazenda
from app.models.parametro import Parametro
from app.models.rebanho import Animal
from app.services.indicador_util import upsert_indicador

CATEGORIAS_MATRIZ = ("Matriz", "Vaca")
TIPOS_MATRIZ = ("Nelore puro", "F1", "T-Cross", "Girolando", "Cruzada", "Outro")


def _meta(db: Session, fazenda: Fazenda, chave: str) -> float | None:
    p = db.execute(
        select(Parametro).where(Parametro.fazenda_id == fazenda.id, Parametro.chave == chave)
    ).scalar_one_or_none()
    return float(p.valor) if p else None


def registrar_desmama(db: Session, animal: Animal, peso: float, data_ref: date | None = None) -> Animal:
    animal.desmama_peso = peso
    animal.desmama_data = data_ref or date.today()
    db.commit()
    db.refresh(animal)
    return animal


def resumo_desmama(db: Session, fazenda: Fazenda) -> dict:
    ativos = select(Animal).where(Animal.fazenda_id == fazenda.id, Animal.status == "ativo")

    matrizes = list(db.execute(ativos.where(Animal.categoria.in_(CATEGORIAS_MATRIZ))).scalars())
    bezerros = list(db.execute(ativos.where(Animal.categoria == "Bezerro")).scalars())
    desmamados = [b for b in bezerros if b.desmama_peso is not None]

    peso_medio = (
        round(sum(float(b.desmama_peso) for b in desmamados) / len(desmamados), 1)
        if desmamados else None
    )
    taxa = round(len(bezerros) / len(matrizes), 4) if matrizes else None

    por_tipo: dict[str, int] = {}
    for m in matrizes:
        chave = m.tipo_matriz or "Nao informado"
        por_tipo[chave] = por_tipo.get(chave, 0) + 1

    hoje = date.today()
    if peso_medio is not None:
        upsert_indicador(db, fazenda.id, "peso_desmama_real", peso_medio, hoje)
    if taxa is not None:
        upsert_indicador(db, fazenda.id, "taxa_desmama", taxa, hoje)
    if peso_medio is not None or taxa is not None:
        db.commit()

    return {
        "matrizes": len(matrizes),
        "bezerros": len(bezerros),
        "desmamados": len(desmamados),
        "taxa_desmama": taxa,
        "taxa_desmama_meta": _meta(db, fazenda, "taxa_desmama_meta"),
        "peso_medio_desmama": peso_medio,
        "peso_desmama_meta": _meta(db, fazenda, "peso_desmama"),
        "por_tipo_matriz": por_tipo,
    }


def bezerros_da_matriz(db: Session, fazenda: Fazenda, matriz: Animal) -> list[Animal]:
    """Vinculo matriz -> bezerro pelo brinco da mae (audio 7)."""
    if not matriz.brinco:
        return []
    return list(db.execute(
        select(Animal).where(
            Animal.fazenda_id == fazenda.id, Animal.mae_brinco == matriz.brinco
        ).order_by(Animal.data_nascimento.desc().nullslast())
    ).scalars())
