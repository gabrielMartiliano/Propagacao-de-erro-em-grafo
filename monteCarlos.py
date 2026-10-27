
"""Experimento de Monte Carlo para avaliar a propagação de erros.

Os casos e suas expressões são definidos em casos.py.
Este arquivo executa as simulações e salva os resultados em CSV.
"""

import csv
import random
import statistics
from pathlib import Path

from motor import Motor
from casos import CASOS


def executar_experimento(
    n_simulacoes=1000,
    deltas=(0.01, 0.1, 0.5),
    semente=20261027,
):
    """Executa o Monte Carlo para todos os casos cadastrados."""

    if n_simulacoes <= 0:
        raise ValueError("n_simulacoes precisa ser maior que zero.")

    if not deltas:
        raise ValueError("Informe pelo menos um valor de delta.")

    if any(delta < 0 for delta in deltas):
        raise ValueError("Os valores de delta não podem ser negativos.")

    gerador = random.Random(semente)
    resultados = []

    for construtor in CASOS:
        caso_base = construtor()
        nome_caso = caso_base["nome"]
        entradas = caso_base["entradas_mc"]

        for delta in deltas:
            erros_reais = []
            erros_lineares = []
            diferencas = []
            coberturas = []

            for _ in range(n_simulacoes):
                # Cria um caso novo para cada simulação.
                caso = construtor()
                motor = Motor(caso["nos"])

                # Perturba cada entrada em até +/- delta
                # em relação ao seu valor nominal.
                perturbacoes = {
                    nome: gerador.uniform(-delta, delta)
                    for nome in entradas
                }

                analise = motor.analisar_perturbacoes(
                    caso["saida"],
                    perturbacoes,
                )

                erro_real = analise["erro_absoluto_real"]
                erro_linear = analise["erro_absoluto_linear"]
                soma_modulos = analise["soma_modulos_contribuicoes"]

                erros_reais.append(erro_real)
                erros_lineares.append(erro_linear)
                diferencas.append(
                    analise["modulo_diferenca_real_linear"]
                )
                coberturas.append(soma_modulos >= erro_real)

            erros_ordenados = sorted(erros_reais)

            indice_p90 = min(
                int(0.90 * len(erros_ordenados)),
                len(erros_ordenados) - 1,
            )
            indice_p99 = min(
                int(0.99 * len(erros_ordenados)),
                len(erros_ordenados) - 1,
            )

            resultados.append({
                "caso": nome_caso,
                "delta": delta,
                "simulacoes": n_simulacoes,
                "erro_real_medio": statistics.mean(erros_reais),
                "erro_real_mediano": statistics.median(erros_reais),
                "erro_real_maximo": max(erros_reais),
                "erro_real_p90": erros_ordenados[indice_p90],
                "erro_real_p99": erros_ordenados[indice_p99],
                "erro_linear_medio": statistics.mean(erros_lineares),
                "diferenca_media_real_linear": statistics.mean(diferencas),
                "cobertura_soma_modulos_percentual": (
                    100.0 * sum(coberturas) / n_simulacoes
                ),
            })

    return resultados


def salvar_csv(resultados, caminho="resultados_monte_carlo.csv"):
    """Salva os resultados agregados em um arquivo CSV."""

    if not resultados:
        raise ValueError("Não há resultados para salvar.")

    caminho = Path(caminho)

    with caminho.open("w", newline="", encoding="utf-8-sig") as arquivo:
        escritor = csv.DictWriter(
            arquivo,
            fieldnames=list(resultados[0].keys()),
        )
        escritor.writeheader()
        escritor.writerows(resultados)

    return caminho


def main():
    n_simulacoes = 1000
    deltas = (0.01, 0.1, 0.5)

    resultados = executar_experimento(
        n_simulacoes=n_simulacoes,
        deltas=deltas,
        semente=20261027,
    )

    arquivo = salvar_csv(resultados)

    print(f"Simulações por caso e delta: {n_simulacoes}")
    print(f"Casos analisados: {len(CASOS)}")
    print(f"Combinações caso/delta: {len(resultados)}")
    print(f"Total de simulações: {len(CASOS) * len(deltas) * n_simulacoes}")
    print(f"Resultados salvos em: {arquivo.resolve()}")

    for linha in resultados:
        print(f"\nCaso: {linha['caso']} | delta={linha['delta']}")
        print(f"  Erro médio: {linha['erro_real_medio']:.6g}")
        print(f"  Erro mediano: {linha['erro_real_mediano']:.6g}")
        print(f"  Erro máximo: {linha['erro_real_maximo']:.6g}")
        print(f"  P90: {linha['erro_real_p90']:.6g}")
        print(f"  P99: {linha['erro_real_p99']:.6g}")
        print(f"  Erro linear médio: {linha['erro_linear_medio']:.6g}")
        print(
            f"  Diferença média real-linear: "
            f"{linha['diferenca_media_real_linear']:.6g}"
        )
        print(
            f"  Cobertura da soma dos módulos: "
            f"{linha['cobertura_soma_modulos_percentual']:.1f}%"
        )


if __name__ == "__main__":
    main()
