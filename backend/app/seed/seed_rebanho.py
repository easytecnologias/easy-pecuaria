"""Seed do rebanho de exemplo na Fazenda Sede: lotes, animais e um historico de
pesagens (2 por animal) para o GMD ja nascer calculado.

Rodar:  python -m app.seed.seed_rebanho
Idempotente: se ja houver lotes na Sede, ignora.
"""

from __future__ import annotations

from datetime import date, timedelta

from sqlalchemy import select

from app.core.db import SessionLocal
from app.models.organizacao import Fazenda
from app.models.rebanho import Animal, Lote, Pesagem
from app.services.rebanho import recomputar_indicadores_rebanho, registrar_pesagem

# lote -> (categoria, local, [(brinco, raca, sexo, peso_ant, peso_atual)])
REBANHO = {
    "Matrizes IATF 1": ("Matrizes", "Pasto 3", [
        ("JLN-0421", "Nelore PO", "F", 455, 472),
        ("JLN-0508", "Nelore", "F", 448, 461),
        ("JLN-0333", "Nelore", "F", 430, 438),
    ]),
    "Garrotes Confinamento A": ("Engorda", "Curral 1", [
        ("JLN-1201", "F1 Angus", "M", 448, 470),   # GMD alto
        ("JLN-1202", "F1 Angus", "M", 452, 448),   # perdeu peso -> GMD negativo
        ("JLN-1210", "F1 Angus", "M", 440, 459),
        ("JLN-1233", "Nelore", "M", 435, 441),     # GMD baixo
    ]),
    "Bezerros Desmama 2026": ("Bezerros", "Pasto 5", [
        ("JLN-2044", "F1 Angus", "M", 205, 218),
        ("JLN-2066", "Nelore", "M", 210, 224),
    ]),
    "Novilhas Reposicao": ("Novilhas", "Pasto 2", [
        ("JLN-1780", "Nelore PO", "F", 330, 342),
    ]),
}

# brinco -> (nascimento, mae_brinco, pai) para a ficha do animal
GENEALOGIA = {
    "JLN-0421": (date(2021, 9, 12), "JLN-0088", "REM Eliseu"),
    "JLN-0508": (date(2020, 8, 3), "JLN-0102", "Nelore CV"),
    "JLN-0333": (date(2019, 10, 20), "JLN-0041", "Nelore CV"),
    "JLN-1201": (date(2024, 7, 15), "JLN-0421", "Angus FP"),
    "JLN-1202": (date(2024, 8, 1), "JLN-0508", "Angus FP"),
    "JLN-1210": (date(2024, 7, 22), "JLN-0333", "Angus FP"),
    "JLN-1233": (date(2024, 9, 5), "JLN-0333", "Nelore CV"),
    "JLN-2044": (date(2025, 10, 10), "JLN-0421", "Angus FP"),
    "JLN-2066": (date(2025, 11, 2), "JLN-0508", "Nelore CV"),
    "JLN-1780": (date(2022, 6, 18), "JLN-0333", "Nelore PO"),
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
        if db.execute(select(Lote).where(Lote.fazenda_id == sede.id)).first():
            print("Rebanho da Sede ja semeado — ignorado.")
            return

        hoje = date.today()
        d_ant = hoje - timedelta(days=28)
        total_animais = 0

        for nome, (categoria, local, animais) in REBANHO.items():
            lote = Lote(fazenda_id=sede.id, nome=nome, categoria=categoria, local=local)
            db.add(lote)
            db.flush()
            for brinco, raca, sexo, peso_ant, peso_atual in animais:
                nasc, mae, pai = GENEALOGIA.get(brinco, (None, None, None))
                animal = Animal(
                    fazenda_id=sede.id, lote_id=lote.id, brinco=brinco,
                    raca=raca, sexo=sexo,
                    categoria={"Matrizes": "Matriz", "Engorda": "Garrote",
                               "Bezerros": "Bezerro", "Novilhas": "Novilha"}[categoria],
                    origem="nascido", status="ativo",
                    data_nascimento=nasc, mae_brinco=mae, pai=pai,
                )
                db.add(animal)
                db.flush()
                # duas pesagens: a antiga (base) e a atual (gera GMD)
                registrar_pesagem(db, animal, d_ant, peso_ant)
                registrar_pesagem(db, animal, hoje, peso_atual)
                total_animais += 1
        db.commit()

        resultado = recomputar_indicadores_rebanho(db, sede)
        print("Rebanho semeado na Fazenda Sede:")
        print(f"  Lotes: {len(REBANHO)} | Animais: {total_animais}")
        print(f"  Pesagens: {total_animais * 2}")
        print(f"  Indicadores recalculados: GMD={resultado['gmd']} | "
              f"ocupacao={resultado['ocupacao_confinamento']} "
              f"({resultado['n_confinamento']} em confinamento)")
    finally:
        db.close()


if __name__ == "__main__":
    run()
