"""Partos: registrar nascimento de uma matriz. Se nasce vivo, cria o bezerro no
rebanho (Animal) já ligado à mãe — alimenta a evolução do rebanho e a natalidade.
"""

from __future__ import annotations

from datetime import date, timedelta

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.organizacao import Fazenda
from app.models.parto import Parto
from app.models.rebanho import Animal
from app.services.rebanho import recomputar_indicadores_rebanho

RESULTADOS = ("nascido_vivo", "natimorto")


def registrar_parto(
    db: Session, fazenda: Fazenda, mae: Animal, data_ref: date, resultado: str,
    sexo_bezerro: str | None, brinco_bezerro: str | None,
    peso_nascimento: float | None, observacao: str | None,
) -> Parto:
    bezerro_id = None
    if resultado == "nascido_vivo":
        sexo = (sexo_bezerro or "").upper()
        if sexo not in ("M", "F"):
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Informe o sexo do bezerro (M ou F).")
        brinco = (brinco_bezerro or "").strip()
        if not brinco:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Informe o brinco do bezerro.")
        ja = db.execute(
            select(Animal).where(Animal.fazenda_id == fazenda.id, Animal.brinco == brinco)
        ).scalar_one_or_none()
        if ja:
            raise HTTPException(status.HTTP_409_CONFLICT, "Já existe animal com esse brinco.")
        bezerro = Animal(
            fazenda_id=fazenda.id, lote_id=mae.lote_id, brinco=brinco,
            categoria="Bezerra" if sexo == "F" else "Bezerro",
            raca=mae.raca, sexo=sexo, data_nascimento=data_ref,
            mae_brinco=mae.brinco, origem="nascido", status="ativo",
        )
        db.add(bezerro)
        db.flush()
        bezerro_id = bezerro.id

    parto = Parto(
        fazenda_id=fazenda.id, mae_id=mae.id, bezerro_id=bezerro_id,
        data=data_ref, resultado=resultado,
        sexo_bezerro=(sexo_bezerro or "").upper() or None,
        brinco_bezerro=(brinco_bezerro or "").strip() or None,
        peso_nascimento=peso_nascimento, observacao=observacao,
    )
    db.add(parto)
    db.commit()
    recomputar_indicadores_rebanho(db, fazenda)  # novo animal muda composição/ocupação
    return parto


def resumo_partos(db: Session, fazenda: Fazenda) -> dict:
    desde12 = date.today() - timedelta(days=365)

    def conta(resultado=None, desde=None):
        stmt = select(func.count(Parto.id)).where(Parto.fazenda_id == fazenda.id)
        if resultado is not None:
            stmt = stmt.where(Parto.resultado == resultado)
        if desde is not None:
            stmt = stmt.where(Parto.data >= desde)
        return int(db.execute(stmt).scalar_one())

    partos_12m = conta(desde=desde12)
    vivos_12m = conta("nascido_vivo", desde12)
    natimortos_12m = conta("natimorto", desde12)
    taxa_natimort = round(natimortos_12m / partos_12m, 4) if partos_12m else None

    # matrizes ativas (base da natalidade)
    matrizes = int(db.execute(
        select(func.count(Animal.id)).where(
            Animal.fazenda_id == fazenda.id, Animal.status == "ativo",
            Animal.sexo == "F", Animal.categoria == "Matriz",
        )
    ).scalar_one())
    taxa_natalidade = round(vivos_12m / matrizes, 4) if matrizes else None

    return {
        "partos_12m": partos_12m, "vivos_12m": vivos_12m, "natimortos_12m": natimortos_12m,
        "taxa_natimortalidade": taxa_natimort, "matrizes": matrizes,
        "taxa_natalidade": taxa_natalidade,
    }
