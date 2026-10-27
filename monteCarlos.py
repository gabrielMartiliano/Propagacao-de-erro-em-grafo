
"""Monte Carlo para propagacao de erros em grafos aritmeticos.

Gera:
- monte_carlo_amostras.csv: uma linha por simulacao;
- monte_carlo_resumo.csv: metricas agregadas por caso e delta.

As perturbacoes sao aditivas e uniformes em [-delta, delta].
"""

import csv
import json
import math
import random
import statistics
from pathlib import Path

from motor import Motor
from casos import CASOS


N_SIMULACOES = 1000
DELTAS = (0.01, 0.1, 0.5)
SEMENTE = 20261027
TOLERANCIA_COBERTURA = 1e-12

# Salva os resultados junto a este arquivo.
PASTA_SAIDA = Path(__file__).resolve().parent


def quantil_nearest_rank(valores, p):
    """Calcula quantil pelo metodo nearest-rank."""
    if not valores:
        raise ValueError("A lista de valores nao pode estar vazia.")

    if not 0 <= p <= 1:
        raise ValueError("p precisa estar entre 0 e 1.")

    ordenados = sorted(valores)
    indice = max(0, math.ceil(p * len(ordenados)) - 1)
    return ordenados[indice]


def executar_experimento(
    n_simulacoes=N_SIMULACOES,
    deltas=DELTAS,
    semente=SEMENTE,
):
    if n_simulacoes <= 0:
        raise ValueError("n_simulacoes precisa ser maior que zero.")

    if not deltas:
        raise ValueError("Informe pelo menos um valor de delta.")

    if any(delta < 0 for delta in deltas):
        raise ValueError("Os valores de delta nao podem ser negativos.")

    gerador = random.Random(semente)
    amostras = []
    resumos = []

    for construtor in CASOS:
        caso_base = construtor()
        nome_caso = caso_base["nome"]
        nomes_perturbados = tuple(caso_base["entradas_mc"].keys())

        for delta in deltas:
            erros_reais = []
            erros_lineares = []
            diferencas_magnitude = []
            coberturas = []

            for numero_amostra in range(1, n_simulacoes + 1):
                # Cria um grafo novo para cada simulacao.
                caso = construtor()
                motor = Motor(caso["nos"])

                perturbacoes = {
                    nome: gerador.uniform(-delta, delta)
                    for nome in nomes_perturbados
                }

                analise = motor.analisar_perturbacoes(
                    caso["saida"],
                    perturbacoes,
                )

                # Nomes correspondentes ao retorno real do motor.py.
                variacao_real = float(analise["variacao_real"])
                variacao_linear = float(
                    analise["variacao_linear_estimada"]
                )

                erro_real = float(analise["erro_absoluto_real"])
                erro_linear = float(analise["erro_absoluto_linear"])

                soma_modulos = float(
                    analise["soma_modulos_contribuicoes"]
                )

                residuo = variacao_real - variacao_linear

                # Diferenca entre os modulos das duas variacoes.
                diferenca_magnitude = abs(erro_real - erro_linear)

                # Verifica se a soma dos modulos das contribuicoes
                # lineares cobre o modulo da variacao real observada.
                coberto = (
                    soma_modulos + TOLERANCIA_COBERTURA >= erro_real
                )

                erros_reais.append(erro_real)
                erros_lineares.append(erro_linear)
                diferencas_magnitude.append(diferenca_magnitude)
                coberturas.append(coberto)

                amostras.append({
                    "caso": nome_caso,
                    "delta": delta,
                    "semente": semente,
                    "n_simulacoes_planejadas": n_simulacoes,
                    "amostra": numero_amostra,
                    "nos_perturbados": json.dumps(
                        list(nomes_perturbados),
                        ensure_ascii=False,
                    ),
                    "perturbacoes": json.dumps(
                        perturbacoes,
                        ensure_ascii=False,
                        sort_keys=True,
                    ),
                    "variacao_real_assinada": variacao_real,
                    "variacao_linear_assinada": variacao_linear,
                    "erro_absoluto_real": erro_real,
                    "erro_absoluto_linear": erro_linear,
                    "diferenca_magnitude_real_linear": (
                        diferenca_magnitude
                    ),
                    "residuo_assinado_real_menos_linear": residuo,
                    "soma_modulos_contribuicoes": soma_modulos,
                    "soma_modulos_cobre_erro_real": int(coberto),
                })

            resumos.append({
                "caso": nome_caso,
                "delta": delta,
                "n_simulacoes": n_simulacoes,
                "semente": semente,
                "erro_real_medio": statistics.mean(erros_reais),
                "erro_real_p50": quantil_nearest_rank(
                    erros_reais, 0.50
                ),
                "erro_real_p90": quantil_nearest_rank(
                    erros_reais, 0.90
                ),
                "erro_real_p99": quantil_nearest_rank(
                    erros_reais, 0.99
                ),
                "erro_real_maximo": max(erros_reais),
                "erro_linear_medio": statistics.mean(erros_lineares),
                "diferenca_magnitude_media_real_linear": (
                    statistics.mean(diferencas_magnitude)
                ),
                "cobertura_soma_modulos_percentual": (
                    100.0 * sum(coberturas) / len(coberturas)
                ),
            })

    return amostras, resumos


def salvar_csv(linhas, caminho):
    """Salva os resultados em CSV."""
    if not linhas:
        raise ValueError(f"Nao ha dados para salvar: {caminho}")

    caminho = Path(caminho)
    caminho.parent.mkdir(parents=True, exist_ok=True)

    with caminho.open(
        "w",
        newline="",
        encoding="utf-8-sig",
    ) as arquivo:
        escritor = csv.DictWriter(
            arquivo,
            fieldnames=list(linhas[0].keys()),
        )
        escritor.writeheader()
        escritor.writerows(linhas)

    return caminho


def main():
    print("Iniciando experimento de Monte Carlo...")

    amostras, resumos = executar_experimento()

    arquivo_amostras = salvar_csv(
        amostras,
        PASTA_SAIDA / "monte_carlo_amostras.csv",
    )

    arquivo_resumo = salvar_csv(
        resumos,
        PASTA_SAIDA / "monte_carlo_resumo.csv",
    )

    print()
    print("Experimento concluido.")
    print(f"Casos: {len(CASOS)}")
    print(f"Deltas: {DELTAS}")
    print(f"Simulacoes por caso/delta: {N_SIMULACOES}")
    print(f"Total de amostras: {len(amostras)}")
    print(f"Semente aleatoria: {SEMENTE}")
    print(f"Amostras individuais: {arquivo_amostras}")
    print(f"Resumo agregado: {arquivo_resumo}")
    print()

    for linha in resumos:
        print(
            f"{linha['caso']} | "
            f"delta={linha['delta']} | "
            f"media={linha['erro_real_medio']:.6g} | "
            f"P50={linha['erro_real_p50']:.6g} | "
            f"P90={linha['erro_real_p90']:.6g} | "
            f"P99={linha['erro_real_p99']:.6g} | "
            f"cobertura="
            f"{linha['cobertura_soma_modulos_percentual']:.1f}%"
        )


if __name__ == "__main__":
    main()
