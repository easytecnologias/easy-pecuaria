"""Seed de inseminações de exemplo na Fazenda Sede (matrizes já semeadas).
Rodar: python -m app.seed.seed_reproducao  — idempotente.
"""

from __future__ import annotations

from datetime import date, timedelta

from sqlalchemy import select

from app.core.db import SessionLocal
from app.models.organizacao import Fazenda
from app.models.rebanho import Animal
from app.models.reproducao import Inseminacao
from app.services.reproducao import recomputar_taxa_prenhez

# brinco -> (touro, inseminador, resultado)
PLANO = {
    "JLN-0421": ("Angus FP", "Vet. Rocha", "prenhe"),
    "JLN-0508": ("Angus FP", "Vet. Rocha", "prenhe"),
    "JLN-0333": ("Hereford", "Insem. Celio", "vazia"),
}


def run() -> None:
    db = SessionLocal()
    try:
        sede = db.execute(
            select(Fazenda).where(Fazenda.nome == "Fazenda Sede - Arapiraca")
        ).scalar_one_or_none()
        if sede is None:
            print("Fazenda Sede nao encontrada — rode o seed principal antes.")
            return
        if db.execute(select(Inseminacao).where(Inseminacao.fazenda_id == sede.id)).first():
            print("Inseminacoes da Sede ja semeadas — ignorado.")
            return

        d = date.today() - timedelta(days=40)
        dg = date.today() - timedelta(days=5)
        n = 0
        for brinco, (touro, insem, resultado) in PLANO.items():
            animal = db.execute(
                select(Animal).where(Animal.fazenda_id == sede.id, Animal.brinco == brinco)
            ).scalar_one_or_none()
            if not animal:
                continue
            db.add(Inseminacao(
                fazenda_id=sede.id, animal_id=animal.id, data=d, touro=touro,
                inseminador=insem, protocolo="IATF", resultado=resultado, dg_data=dg,
            ))
            n += 1
        db.commit()
        taxa = recomputar_taxa_prenhez(db, sede)
        print(f"Inseminacoes semeadas: {n} | taxa de prenhez calculada: {taxa}")
    finally:
        db.close()


if __name__ == "__main__":
    run()
