"""Nucleo puro do motor de gatilhos: dado um operador, um valor observado e uma
referencia, decide se a regra dispara. Sem dependencia de banco — testavel isolado.
"""

from app.models.enums import Operador


def dispara(
    operador: Operador,
    valor: float | None,
    referencia: float | None,
    tolerancia: float | None = None,
) -> bool:
    """Retorna True se a condicao da regra for satisfeita (ou seja, gera alerta).

    valor       -> ultimo valor do indicador na fazenda
    referencia  -> limite (valor fixo ou vindo de um parametro da fazenda)
    tolerancia  -> usado apenas no operador abs_diff> (desvio absoluto)
    """
    if valor is None or referencia is None:
        return False

    match operador:
        case Operador.gt:
            return valor > referencia
        case Operador.gte:
            return valor >= referencia
        case Operador.lt:
            return valor < referencia
        case Operador.lte:
            return valor <= referencia
        case Operador.eq:
            return valor == referencia
        case Operador.ne:
            return valor != referencia
        case Operador.abs_diff_gt:
            return abs(valor - referencia) > (tolerancia or 0.0)
    return False


def texto_condicao(
    operador: Operador,
    referencia: float | None,
    tolerancia: float | None = None,
) -> str:
    """Descricao legivel da condicao, para exibir no alerta/dashboard."""
    if operador == Operador.abs_diff_gt:
        return f"desvio absoluto da meta > {tolerancia}"
    ref = "meta" if referencia is None else referencia
    return f"valor {operador.value} {ref}"
