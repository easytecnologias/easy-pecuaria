import enum


class PapelUsuario(str, enum.Enum):
    direcao = "direcao"
    gerente = "gerente"
    campo = "campo"
    vet = "vet"
    admin = "admin"


class Severidade(str, enum.Enum):
    ok = "OK"
    revisar = "REVISAR"
    avaliar = "AVALIAR"
    alerta = "ALERTA"
    critico = "CRITICO"


class Operador(str, enum.Enum):
    gt = ">"          # valor > referencia
    gte = ">="        # valor >= referencia
    lt = "<"          # valor < referencia
    lte = "<="        # valor <= referencia
    eq = "=="         # valor == referencia
    ne = "!="         # valor != referencia
    abs_diff_gt = "abs_diff>"  # |valor - referencia| > tolerancia (usa 'tolerancia')


class TipoReferencia(str, enum.Enum):
    valor_fixo = "valor_fixo"   # limite e um numero na propria regra
    parametro = "parametro"     # limite vem de um Parametro da fazenda (por chave)


class OrigemValor(str, enum.Enum):
    manual = "manual"
    integracao = "integracao"
    calculo = "calculo"


class StatusAlerta(str, enum.Enum):
    aberto = "aberto"
    resolvido = "resolvido"


class FormatoIndicador(str, enum.Enum):
    numero = "numero"
    percentual = "percentual"
    moeda = "moeda"
    dias = "dias"
