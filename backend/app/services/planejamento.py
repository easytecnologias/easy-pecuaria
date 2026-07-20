"""Planejamento de atividades (audio 13 do cliente).

Lanca atividade -> define responsavel -> a pessoa ve o que tem para executar
-> marca concluida -> o gestor acompanha os numeros.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.organizacao import Fazenda
from app.models.planejamento import Atividade
from app.models.usuario import Usuario

ABERTAS = ("pendente", "em_andamento")


def listar(
    db: Session, fazenda: Fazenda, periodo: str | None = None,
    status: str | None = None, responsavel_id=None,
) -> list[Atividade]:
    stmt = select(Atividade).where(Atividade.fazenda_id == fazenda.id)
    if periodo:
        stmt = stmt.where(Atividade.periodo == periodo)
    if status:
        stmt = stmt.where(Atividade.status == status)
    if responsavel_id:
        stmt = stmt.where(Atividade.responsavel_id == responsavel_id)
    return list(db.execute(stmt.order_by(Atividade.data_prevista)).scalars())


def criar(db: Session, fazenda: Fazenda, dados: dict, criador: Usuario) -> Atividade:
    resp_nome = None
    if dados.get("responsavel_id"):
        resp = db.get(Usuario, dados["responsavel_id"])
        resp_nome = resp.nome if resp else None
    a = Atividade(
        fazenda_id=fazenda.id,
        criado_por_nome=getattr(criador, "nome", None) or getattr(criador, "email", None),
        responsavel_nome=resp_nome,
        **dados,
    )
    db.add(a)
    db.commit()
    db.refresh(a)
    return a


def concluir(db: Session, a: Atividade, usuario: Usuario, obs: str | None = None) -> Atividade:
    a.status = "concluida"
    a.concluida_em = datetime.now(timezone.utc)
    a.concluida_por_nome = getattr(usuario, "nome", None) or getattr(usuario, "email", None)
    a.observacao_conclusao = obs
    db.commit()
    db.refresh(a)
    return a


def resumo(db: Session, fazenda: Fazenda, usuario: Usuario | None = None) -> dict:
    todas = listar(db, fazenda)
    hoje = date.today()
    prox7 = hoje + timedelta(days=7)

    abertas = [a for a in todas if a.status in ABERTAS]
    concluidas = [a for a in todas if a.status == "concluida"]
    atrasadas = [a for a in abertas if a.data_prevista < hoje]
    semana = [a for a in abertas if hoje <= a.data_prevista <= prox7]

    # "minhas" = o que ESTA pessoa precisa executar
    minhas = [a for a in abertas if usuario and a.responsavel_id == usuario.id] if usuario else []

    total_ciclo = len(concluidas) + len(abertas)
    taxa = round(len(concluidas) / total_ciclo, 4) if total_ciclo else None

    por_periodo: dict[str, int] = {}
    for a in abertas:
        por_periodo[a.periodo] = por_periodo.get(a.periodo, 0) + 1

    return {
        "total": len(todas),
        "abertas": len(abertas),
        "concluidas": len(concluidas),
        "atrasadas": len(atrasadas),
        "da_semana": len(semana),
        "minhas_pendentes": len(minhas),
        "taxa_conclusao": taxa,
        "por_periodo": por_periodo,
        "atividades": todas,
    }
