
"""Casos de referência para o projeto de propagação de erros.

Os quatro casos são definidos com valores esperados calculados à mão.
O main.py e o monteCarlos.py reutilizam os casos deste arquivo.
"""

from motor import No


def caso_1():
    """Perturbação em nó intermediário: z = (a + b) * c."""

    a = No("a", "INPUT", 2.0)
    b = No("b", "INPUT", 3.0)
    c = No("c", "INPUT", 10.0)

    soma = No("soma", "ADD", entradas=[a, b])
    saida = No("saida", "MUL", entradas=[soma, c])

    return {
        "nome": "Caso 1 - Perturbacao em no intermediario",
        "nos": [a, b, c, soma, saida],
        "saida": saida,
        "entradas_mc": {"a": 2.0, "b": 3.0, "c": 10.0},
        "perturbacoes_teste": {"soma": 0.5},
        "saida_esperada": 50.0,
        "saida_perturbada_esperada": 55.0,
        "sensibilidade_esperada": {"soma": 10.0},
        "descricao": "Verifica a propagacao de perturbacao em no intermediario.",
    }


def caso_2():
    """Caso nao linear: z = a * a, com delta = 0.5."""

    a = No("a", "INPUT", 2.0)
    saida = No("saida", "MUL", entradas=[a, a])

    delta = 0.5

    # z = 2^2 = 4
    # z_perturbado = (2 + 0.5)^2 = 6.25
    # Erro real assinado = 6.25 - 4 = 2.25
    # Aproximacao de primeira ordem = 2*a*delta = 2
    # Diferenca = delta^2 = 0.25

    return {
        "nome": "Caso 2 - Erro nao linear z = a * a",
        "nos": [a, saida],
        "saida": saida,
        "entradas_mc": {"a": 2.0},
        "perturbacoes_teste": {"a": delta},
        "saida_esperada": 4.0,
        "saida_perturbada_esperada": 6.25,
        "sensibilidade_esperada": {"a": 4.0},
        "delta_esperado": delta,
        "erro_real_assinado_esperado": 2.25,
        "erro_linear_assinado_esperado": 2.0,
        "diferenca_real_linear_esperada": 0.25,
        "descricao": (
            "Compara o erro real com a aproximacao linear; "
            "o termo de segunda ordem e delta^2 = 0.25."
        ),
    }


def caso_3():
    """Caminhos convergentes: z = (a + b) * (a * b)."""

    a = No("a", "INPUT", 2.0)
    b = No("b", "INPUT", 3.0)

    soma = No("soma", "ADD", entradas=[a, b])
    produto = No("produto", "MUL", entradas=[a, b])
    saida = No("saida", "MUL", entradas=[soma, produto])

    delta = 0.5

    # z = (2 + 3) * (2 * 3) = 30
    # z_perturbado = (2.5 + 3) * (2.5 * 3) = 41.25
    # Erro real assinado = 11.25
    # dz/da = b(a+b) + ab = 2ab + b^2 = 21
    # Estimativa linear = 21 * 0.5 = 10.5
    # Diferenca = 11.25 - 10.5 = 0.75

    return {
        "nome": "Caso 3 - Caminhos convergentes",
        "nos": [a, b, soma, produto, saida],
        "saida": saida,
        "entradas_mc": {"a": 2.0, "b": 3.0},
        "perturbacoes_teste": {"a": delta},
        "saida_esperada": 30.0,
        "saida_perturbada_esperada": 41.25,
        "sensibilidade_esperada": {
            "a": 21.0,
            "b": 16.0,
        },
        "delta_esperado": delta,
        "erro_real_assinado_esperado": 11.25,
        "erro_linear_assinado_esperado": 10.5,
        "diferenca_real_linear_esperada": 0.75,
        "descricao": (
            "A entrada a afeta os ramos soma e produto, "
            "que convergem na saida."
        ),
    }


def caso_4():
    """Divisao com denominador longe de zero: z = a / b."""

    a = No("a", "INPUT", 12.0)
    b = No("b", "INPUT", 3.0)
    saida = No("saida", "DIV", entradas=[a, b])

    delta_b = 0.1
    valor_perturbado = 12.0 / (3.0 + delta_b)

    return {
        "nome": "Caso 4 - Divisao em dominio valido",
        "nos": [a, b, saida],
        "saida": saida,
        "entradas_mc": {"a": 12.0, "b": 3.0},
        "perturbacoes_teste": {"b": delta_b},
        "saida_esperada": 4.0,
        "saida_perturbada_esperada": valor_perturbado,
        "sensibilidade_esperada": {
            "a": 1.0 / 3.0,
            "b": -4.0 / 3.0,
        },
        "delta_esperado": delta_b,
        "descricao": (
            "Verifica a propagacao de erro na divisao, "
            "mantendo o denominador longe de zero."
        ),
    }


# Lista central dos casos utilizados pelo projeto.
CASOS = [
    caso_1,
    caso_2,
    caso_3,
    caso_4,
]
