"""Servico que aplica o motor de gatilhos a uma fazenda usando os dados do banco:
avalia cada regra da organizacao, resolve o limite por fazenda e sincroniza os alertas.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.avaliacao import dispara, texto_condicao
from app.models.enums import Severidade, StatusAlerta, TipoReferencia
from app.models.gatilho import Alerta, RegraGatilho
from app.models.indicador import IndicadorDefinicao, IndicadorValor
from app.models.organizacao import Fazenda
from app.models.parametro import Parametro


@dataclass
class ResultadoRegra:
    regra: RegraGatilho
    indicador: IndicadorDefinicao
    valor_observado: float | None
    data_valor: date | None
    valor_referencia: float | None
    tolerancia: float | None
    disparou: bool
    severidade: Severidade  # OK quando nao disparou
    mensagem: str
    acao: str | None


def _ultimo_valor(
    db: Session, fazenda_id, indicador_id
) -> tuple[float | None, date | None]:
    row = db.execute(
        select(IndicadorValor.valor, IndicadorValor.data_ref)
        .where(
            IndicadorValor.fazenda_id == fazenda_id,
            IndicadorValor.indicador_id == indicador_id,
        )
        .order_by(IndicadorValor.data_ref.desc())
        .limit(1)
    ).first()
    if row is None:
        return None, None
    return float(row[0]), row[1]


def _resolver_referencia(
    db: Session, fazenda_id, regra: RegraGatilho
) -> tuple[float | None, float | None]:
    """Retorna (referencia, tolerancia) para a regra nesta fazenda."""
    tolerancia = float(regra.tolerancia) if regra.tolerancia is not None else None
    if regra.tipo_referencia == TipoReferencia.valor_fixo:
        ref = float(regra.valor_referencia) if regra.valor_referencia is not None else None
        return ref, tolerancia
    # tipo == parametro: buscar valor do parametro da fazenda pela chave
    valor = db.execute(
        select(Parametro.valor).where(
            Parametro.fazenda_id == fazenda_id,
            Parametro.chave == regra.parametro_chave,
        )
    ).scalar_one_or_none()
    ref = float(valor) if valor is not None else None
    return ref, tolerancia


def avaliar_fazenda(
    db: Session,
    fazenda: Fazenda,
    regras: list[RegraGatilho] | None = None,
    indicadores: dict | None = None,
) -> list[ResultadoRegra]:
    """Avalia todas as regras ativas da organizacao para a fazenda dada.

    Faz apenas 2 queries por fazenda (ultimos valores + parametros) e avalia em
    memoria — evita N+1 (importante sobre o tunel SSH). regras/indicadores podem
    ser passados prontos para nao recarregar a cada fazenda.
    """
    if regras is None:
        regras = list(
            db.execute(
                select(RegraGatilho).where(
                    RegraGatilho.org_id == fazenda.org_id,
                    RegraGatilho.ativo.is_(True),
                )
            ).scalars().all()
        )
    if indicadores is None:
        indicadores = {
            i.id: i for i in db.execute(select(IndicadorDefinicao)).scalars().all()
        }

    # ultimo valor de cada indicador nesta fazenda (1 query, DISTINCT ON)
    ultimos = {
        ind_id: (float(val), data)
        for ind_id, val, data in db.execute(
            select(IndicadorValor.indicador_id, IndicadorValor.valor, IndicadorValor.data_ref)
            .where(IndicadorValor.fazenda_id == fazenda.id)
            .order_by(IndicadorValor.indicador_id, IndicadorValor.data_ref.desc())
            .distinct(IndicadorValor.indicador_id)
        ).all()
    }
    # parametros da fazenda (1 query)
    parametros = {
        chave: float(valor)
        for chave, valor in db.execute(
            select(Parametro.chave, Parametro.valor).where(Parametro.fazenda_id == fazenda.id)
        ).all()
    }

    resultados: list[ResultadoRegra] = []
    for regra in regras:
        indicador = indicadores.get(regra.indicador_id)
        valor, data_valor = ultimos.get(regra.indicador_id, (None, None))
        tol = float(regra.tolerancia) if regra.tolerancia is not None else None
        if regra.tipo_referencia == TipoReferencia.valor_fixo:
            ref = float(regra.valor_referencia) if regra.valor_referencia is not None else None
        else:
            ref = parametros.get(regra.parametro_chave)
        disparou = dispara(regra.operador, valor, ref, tol)
        severidade = regra.severidade if disparou else Severidade.ok

        cond = texto_condicao(regra.operador, ref, tol)
        nome_ind = indicador.nome if indicador else "indicador"
        if valor is None:
            mensagem = f"{nome_ind}: sem dado registrado."
        elif disparou:
            mensagem = f"{nome_ind} = {valor} ({cond})."
        else:
            mensagem = f"{nome_ind} = {valor}: dentro do esperado."

        resultados.append(
            ResultadoRegra(
                regra=regra,
                indicador=indicador,
                valor_observado=valor,
                data_valor=data_valor,
                valor_referencia=ref,
                tolerancia=tol,
                disparou=disparou,
                severidade=severidade,
                mensagem=mensagem,
                acao=regra.acao if disparou else None,
            )
        )
    return resultados


def sincronizar_alertas(db: Session, fazenda: Fazenda) -> list[ResultadoRegra]:
    """Avalia e persiste alertas: abre novos que dispararam, resolve os que voltaram ao normal."""
    resultados = avaliar_fazenda(db, fazenda)
    agora = datetime.now(timezone.utc)

    for r in resultados:
        alerta_aberto = db.execute(
            select(Alerta).where(
                Alerta.fazenda_id == fazenda.id,
                Alerta.regra_id == r.regra.id,
                Alerta.status == StatusAlerta.aberto,
            )
        ).scalar_one_or_none()

        if r.disparou:
            if alerta_aberto is None:
                db.add(
                    Alerta(
                        fazenda_id=fazenda.id,
                        regra_id=r.regra.id,
                        indicador_id=r.regra.indicador_id,
                        severidade=r.severidade,
                        status=StatusAlerta.aberto,
                        valor_observado=r.valor_observado,
                        valor_referencia=r.valor_referencia,
                        mensagem=r.mensagem,
                        acao=r.acao,
                        avaliado_em=agora,
                    )
                )
            else:
                alerta_aberto.valor_observado = r.valor_observado
                alerta_aberto.valor_referencia = r.valor_referencia
                alerta_aberto.mensagem = r.mensagem
                alerta_aberto.severidade = r.severidade
                alerta_aberto.avaliado_em = agora
        elif alerta_aberto is not None:
            alerta_aberto.status = StatusAlerta.resolvido
            alerta_aberto.resolvido_em = agora

    db.commit()
    return resultados
