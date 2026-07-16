"""Seed de estoque de volumoso + uma dieta na Fazenda Sede.
Rodar: python -m app.seed.seed_operacao  — idempotente.
"""

from __future__ import annotations

from datetime import date, timedelta

from sqlalchemy import select

from app.core.db import SessionLocal
from app.models.estoque import MovimentoVolumoso
from app.models.nutricao import Dieta, ItemDieta
from app.models.organizacao import Fazenda
from app.models.rebanho import Lote
from app.services.estoque import recomputar_estoque
from app.services.nutricao import recomputar_indicadores_dieta


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
        # --- estoque de volumoso ---
        if not db.execute(select(MovimentoVolumoso).where(MovimentoVolumoso.fazenda_id == sede.id)).first():
            db.add(MovimentoVolumoso(fazenda_id=sede.id, data=hoje - timedelta(days=45),
                                     tipo="entrada", quantidade_t=600, descricao="Ensilagem milho 2026"))
            for d in (25, 15, 5):
                db.add(MovimentoVolumoso(fazenda_id=sede.id, data=hoje - timedelta(days=d),
                                         tipo="saida", quantidade_t=100, descricao="Consumo cocho"))
            db.commit()
            r = recomputar_estoque(db, sede)
            print(f"Estoque semeado: saldo={r['saldo_t']}t consumo={r['consumo_diario_t']}t/dia dias={r['dias']}")
        else:
            print("Estoque ja semeado — ignorado.")

        # --- dieta do confinamento ---
        if not db.execute(select(Dieta).where(Dieta.fazenda_id == sede.id)).first():
            lote = db.execute(
                select(Lote).where(Lote.fazenda_id == sede.id, Lote.nome == "Garrotes Confinamento A")
            ).scalar_one_or_none()
            dieta = Dieta(fazenda_id=sede.id, lote_id=lote.id if lote else None,
                          nome="Terminacao confinamento", data=hoje, ativa=True)
            dieta.itens = [
                ItemDieta(ingrediente="Silagem de milho", inclusao_kg=14, preco_kg=0.32, ms_pct=0.34),
                ItemDieta(ingrediente="Milho moido", inclusao_kg=4, preco_kg=1.55, ms_pct=0.88),
                ItemDieta(ingrediente="Farelo de soja", inclusao_kg=1.5, preco_kg=2.60, ms_pct=0.89),
            ]
            db.add(dieta)
            db.commit()
            calc = recomputar_indicadores_dieta(db, sede)
            print(f"Dieta semeada: custo/cab/dia=R${calc['custo_cab_dia']} consumo_ms_pv={calc['consumo_ms_pv']}")
        else:
            print("Dieta ja semeada — ignorado.")
    finally:
        db.close()


if __name__ == "__main__":
    run()
