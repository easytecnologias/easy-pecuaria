"""Contas a pagar e a receber (audio 9 do cliente).

"na parte financeira eu preciso que ele tenha contas a pagar e a receber,
lancamentos de notas, acompanhamentos, que ele tenha um aviso para duplicatas,
quando as duplicatas e os boletos estiverem vencendo"

A conta e o compromisso (tem vencimento); o lancamento e o dinheiro que andou.
Ao baixar uma conta o sistema cria o lancamento correspondente, para o saldo e
a margem por cabeca continuarem batendo com a realidade.
"""

from __future__ import annotations

from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.financeiro import ContaFinanceira
from app.models.organizacao import Fazenda
from app.services.financeiro import recomputar_financeiro, registrar_lancamento

# quantos dias antes do vencimento a conta ja entra no aviso
JANELA_AVISO = 7


def listar(
    db: Session, fazenda: Fazenda, tipo: str | None = None, status: str | None = None
) -> list[ContaFinanceira]:
    stmt = select(ContaFinanceira).where(ContaFinanceira.fazenda_id == fazenda.id)
    if tipo:
        stmt = stmt.where(ContaFinanceira.tipo == tipo)
    if status:
        stmt = stmt.where(ContaFinanceira.status == status)
    return list(db.execute(stmt.order_by(ContaFinanceira.vencimento)).scalars())


def situacao(conta: ContaFinanceira, hoje: date | None = None) -> str:
    """aberto -> vencida / vence_em_breve / em_dia; baixado e cancelado passam direto."""
    if conta.status != "aberto":
        return conta.status
    hoje = hoje or date.today()
    if conta.vencimento < hoje:
        return "vencida"
    if conta.vencimento <= hoje + timedelta(days=JANELA_AVISO):
        return "vence_em_breve"
    return "em_dia"


def _dias(conta: ContaFinanceira, hoje: date) -> int:
    """Dias ate o vencimento; negativo quando ja venceu."""
    return (conta.vencimento - hoje).days


def resumo(db: Session, fazenda: Fazenda) -> dict:
    hoje = date.today()
    contas = listar(db, fazenda)
    abertas = [c for c in contas if c.status == "aberto"]

    def soma(itens) -> float:
        return round(sum(float(c.valor) for c in itens), 2)

    a_pagar = [c for c in abertas if c.tipo == "pagar"]
    a_receber = [c for c in abertas if c.tipo == "receber"]
    vencidas = [c for c in abertas if situacao(c, hoje) == "vencida"]
    vencendo = [c for c in abertas if situacao(c, hoje) == "vence_em_breve"]

    linhas = [
        {
            "id": c.id, "tipo": c.tipo, "descricao": c.descricao, "categoria": c.categoria,
            "contraparte": c.contraparte, "documento": c.documento,
            "numero_documento": c.numero_documento, "valor": round(float(c.valor), 2),
            "emissao": c.emissao, "vencimento": c.vencimento, "status": c.status,
            "situacao": situacao(c, hoje), "dias": _dias(c, hoje),
            "data_baixa": c.data_baixa,
            "valor_pago": round(float(c.valor_pago), 2) if c.valor_pago is not None else None,
            "observacao": c.observacao,
        }
        for c in contas
    ]

    return {
        "total_a_pagar": soma(a_pagar),
        "total_a_receber": soma(a_receber),
        "saldo_previsto": round(soma(a_receber) - soma(a_pagar), 2),
        "vencidas": len(vencidas),
        "valor_vencido": soma(vencidas),
        "vencendo": len(vencendo),
        "valor_vencendo": soma(vencendo),
        "janela_aviso_dias": JANELA_AVISO,
        # o que o cliente quer ver primeiro: duplicata/boleto perto do vencimento
        "avisos": [
            f"{c.descricao} ({c.documento}) vence em {_dias(c, hoje)} d"
            if _dias(c, hoje) >= 0
            else f"{c.descricao} ({c.documento}) venceu ha {-_dias(c, hoje)} d"
            for c in sorted(vencidas + vencendo, key=lambda x: x.vencimento)
        ],
        "contas": linhas,
    }


def baixar(
    db: Session, fazenda: Fazenda, conta: ContaFinanceira,
    data_baixa: date | None = None, valor_pago: float | None = None,
) -> ContaFinanceira:
    """Marca a conta como paga/recebida e joga o valor no caixa."""
    if conta.status == "baixado":
        return conta
    data_baixa = data_baixa or date.today()
    valor = float(valor_pago) if valor_pago is not None else float(conta.valor)

    lanc = registrar_lancamento(
        db, fazenda.id, data_baixa,
        "despesa" if conta.tipo == "pagar" else "receita",
        conta.categoria, valor,
        f"{conta.descricao} ({conta.documento})",
    )
    conta.status = "baixado"
    conta.data_baixa = data_baixa
    conta.valor_pago = valor
    conta.lancamento_id = lanc.id
    db.commit()
    recomputar_financeiro(db, fazenda)
    db.refresh(conta)
    return conta
