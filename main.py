
"""Executa os testes determinísticos definidos em casos.py."""

from math import isclose

from motor import Motor
from casos import CASOS

TOLERANCIA = 1e-9


def conferir(valor, esperado):
    return isclose(
        valor,
        esperado,
        rel_tol=TOLERANCIA,
        abs_tol=TOLERANCIA,
    )


def executar_caso(construtor):
    caso = construtor()

    motor = Motor(caso["nos"])
    saida = caso["saida"]

    valor = motor.avaliar(saida)
    sensibilidades = motor.calcular_sensibilidades(saida)

    valor_perturbado = motor.avaliar(
        saida,
        caso["perturbacoes_teste"],
    )

    verificacoes = [
        conferir(valor, caso["saida_esperada"]),
        conferir(
            valor_perturbado,
            caso["saida_perturbada_esperada"],
        ),
    ]

    # Confere as sensibilidades calculadas à mão.
    for nome, esperado in caso["sensibilidade_esperada"].items():
        verificacoes.append(
            conferir(sensibilidades[nome], esperado)
        )

    # Para os casos não lineares, confere também a diferença
    # entre o erro real e a estimativa de primeira ordem.
    if "erro_real_assinado_esperado" in caso:
        erro_real = valor_perturbado - valor

        analise = motor.analisar_perturbacoes(
            saida,
            caso["perturbacoes_teste"],
        )

        # A estimativa linear assinada é calculada a partir
        # das sensibilidades e das perturbações aplicadas.
        erro_linear_assinado = sum(
            sensibilidades[nome] * delta
            for nome, delta in caso["perturbacoes_teste"].items()
        )

        diferenca_assinada = erro_real - erro_linear_assinado

        verificacoes.extend([
            conferir(
                erro_real,
                caso["erro_real_assinado_esperado"],
            ),
            conferir(
                erro_linear_assinado,
                caso["erro_linear_assinado_esperado"],
            ),
            conferir(
                diferenca_assinada,
                caso["diferenca_real_linear_esperada"],
            ),
        ])

        print(f"Erro real assinado: {erro_real:.10g}")
        print(
            f"Erro linear assinado: "
            f"{erro_linear_assinado:.10g}"
        )
        print(
            f"Diferenca real-linear: "
            f"{diferenca_assinada:.10g}"
        )
        print(
            f"Erro absoluto calculado pelo motor: "
            f"{analise['erro_absoluto_real']:.10g}"
        )
        print(
            f"Estimativa linear absoluta do motor: "
            f"{analise['erro_absoluto_linear']:.10g}"
        )

    aprovado = all(verificacoes)

    print(f"\n{caso['nome']}")
    print(f"Descrição: {caso['descricao']}")
    print(f"Saída nominal: {valor:.10g}")
    print(f"Saída perturbada: {valor_perturbado:.10g}")

    print("Sensibilidades:")
    for nome, esperado in caso["sensibilidade_esperada"].items():
        print(
            f"  {nome}: calculada={sensibilidades[nome]:.10g}; "
            f"esperada={esperado:.10g}"
        )

    print(f"Resultado: {'APROVADO' if aprovado else 'FALHOU'}")

    return aprovado


def main():
    resultados = [
        executar_caso(construtor)
        for construtor in CASOS
    ]

    aprovados = sum(resultados)

    print(
        f"\nResumo: {aprovados}/{len(resultados)} "
        f"casos aprovados."
    )

    if aprovados != len(resultados):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
