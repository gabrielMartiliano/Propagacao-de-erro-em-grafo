
"""Executa os casos determinísticos definidos em casos.py."""

from math import isclose

from motor import Motor
from casos import CASOS


TOLERANCIA = 1e-9


def executar_caso(construtor):
    # Chama a função para obter os dados do caso.
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
        isclose(
            valor,
            caso["saida_esperada"],
            rel_tol=TOLERANCIA,
            abs_tol=TOLERANCIA,
        ),
        isclose(
            valor_perturbado,
            caso["saida_perturbada_esperada"],
            rel_tol=TOLERANCIA,
            abs_tol=TOLERANCIA,
        ),
    ]

    for nome, esperado in caso["sensibilidade_esperada"].items():
        verificacoes.append(
            isclose(
                sensibilidades[nome],
                esperado,
                rel_tol=TOLERANCIA,
                abs_tol=TOLERANCIA,
            )
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
    resultados = [executar_caso(construtor) for construtor in CASOS]
    aprovados = sum(resultados)

    print(f"\nResumo: {aprovados}/{len(resultados)} casos aprovados.")

    if aprovados != len(resultados):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
