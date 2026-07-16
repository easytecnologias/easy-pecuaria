"""Seed de mercado: cotação de arroba + preços de insumos na Fazenda Sede.
Rodar: python -m app.seed.seed_mercado — idempotente.
"""

from __future__ import annotations

from datetime import date

from sqlalchemy import select

from app.core.db import SessionLocal
from app.models.mercado import CotacaoArroba, CotacaoInsumo
from app.models.organizacao import Fazenda
from app.services.mercado import registrar_cotacao_arroba

# insumo, praca, unidade, preco_origem, frete, outros, ms_pct
INSUMOS = [
    ("Silagem de milho", "Arapiraca/AL", "t", 260, 25, 8, 0.34),
    ("Milho moido", "Arapiraca/AL", "kg", 1.45, 0.08, 0.02, 0.88),
    ("Farelo de soja", "Maceio/AL", "kg", 2.35, 0.12, 0.03, 0.89),
]


def run() -> None:
    db = SessionLocal()
    try:
        sede = db.execute(
            select(Fazenda).where(Fazenda.nome == "Fazenda Sede - Arapiraca")
        ).scalar_one_or_none()
        if sede is None:
            print("Fazenda Sede nao encontrada.")
            return
        hoje = date.today()

        if not db.execute(select(CotacaoArroba).where(CotacaoArroba.fazenda_id == sede.id)).first():
            registrar_cotacao_arroba(db, sede, hoje, 310)
            print("Arroba semeada: R$ 310/@ -> indicador arroba_recebida")
        else:
            print("Arroba ja semeada.")

        if not db.execute(select(CotacaoInsumo).where(CotacaoInsumo.fazenda_id == sede.id)).first():
            for insumo, praca, un, po, fr, ou, ms in INSUMOS:
                db.add(CotacaoInsumo(
                    fazenda_id=sede.id, data=hoje, insumo=insumo, praca=praca,
                    unidade=un, preco_origem=po, frete=fr, outros=ou, ms_pct=ms,
                ))
            db.commit()
            print(f"Insumos semeados: {len(INSUMOS)}")
        else:
            print("Insumos ja semeados.")
    finally:
        db.close()


if __name__ == "__main__":
    run()
