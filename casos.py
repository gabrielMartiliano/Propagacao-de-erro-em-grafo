
"""Casos de referência para o projeto de propagação de erros.

Para adicionar ou modificar experimentos, altere este arquivo.
O main.py e o monte_carlo.py reutilizam os casos definidos aqui.
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
        "descricao": "Verifica a propagacao de uma perturbacao intermediaria.",
    }


def caso_2():
    """Ramificações convergentes: z = 2*x + 3*x."""

    x = No("x", "INPUT", 4.0)
    dois = No("dois", "INPUT", 2.0)
    tres = No("tres", "INPUT", 3.0)

    ramo_a = No("ramo_a", "MUL", entradas=[x, dois])
    ramo_b = No("ramo_b", "MUL", entradas=[x, tres])
    saida = No("saida", "ADD", entradas=[ramo_a, ramo_b])

    return {
        "nome": "Caso 2 - Ramificacoes convergentes",
        "nos": [x, dois, tres, ramo_a, ramo_b, saida],
        "saida": saida,
        "entradas_mc": {"x": 4.0},
        "perturbacoes_teste": {"x": 0.1},
        "saida_esperada": 20.0,
        "saida_perturbada_esperada": 20.5,
        "sensibilidade_esperada": {"x": 5.0},
        "descricao": "Verifica a soma das contribuicoes de caminhos convergentes.",
    }


def caso_3():
    """Cancelamento entre caminhos: z = 2*x - 2*x."""

    x = No("x", "INPUT", 7.0)
    dois_a = No("dois_a", "INPUT", 2.0)
    dois_b = No("dois_b", "INPUT", 2.0)

    ramo_a = No("ramo_a", "MUL", entradas=[x, dois_a])
    ramo_b = No("ramo_b", "MUL", entradas=[x, dois_b])
    saida = No("saida", "SUB", entradas=[ramo_a, ramo_b])

    return {
        "nome": "Caso 3 - Cancelamento entre caminhos",
        "nos": [x, dois_a, dois_b, ramo_a, ramo_b, saida],
        "saida": saida,
        "entradas_mc": {"x": 7.0},
        "perturbacoes_teste": {"x": 0.25},
        "saida_esperada": 0.0,
        "saida_perturbada_esperada": 0.0,
        "sensibilidade_esperada": {"x": 0.0},
        "descricao": "Verifica o cancelamento das sensibilidades assinadas.",
    }


def caso_4():
    """Divisão em domínio válido: z = a / b."""

    a = No("a", "INPUT", 12.0)
    b = No("b", "INPUT", 3.0)
    saida = No("saida", "DIV", entradas=[a, b])

    return {
        "nome": "Caso 4 - Divisao em dominio valido",
        "nos": [a, b, saida],
        "saida": saida,
        "entradas_mc": {"a": 12.0, "b": 3.0},
        "perturbacoes_teste": {"a": 0.1},
        "saida_esperada": 4.0,
        "saida_perturbada_esperada": 12.1 / 3.0,
        "sensibilidade_esperada": {
            "a": 1.0 / 3.0,
            "b": -4.0 / 3.0,
        },
        "descricao": "Verifica o valor e as derivadas da divisao.",
    }


# Lista central dos casos utilizados pelo projeto.
# Para adicionar um caso, crie uma função acima e inclua-a nesta lista.

CASOS = [
    caso_1,
    caso_2,
    caso_3,
    caso_4,
]
