"""Benchmark end-to-end do Motor.analisar_perturbacoes em cadeias de ADD.

Mede apenas o custo computacional, sem alterar os arquivos originais do motor.
"""
import csv
import platform
import statistics
import sys
import time
from pathlib import Path

from motor import Motor, No

TAMANHOS = [8, 16, 32, 64, 128, 256, 384]
AQUECIMENTO = 5
REPETICOES = 30
SAIDA = Path(__file__).with_name("benchmark_complexidade.csv")


def construir_cadeia(n):
    entradas = [No(f"x{i}", "INPUT", valor=1.0 + (i % 3) * 0.01) for i in range(n)]
    atual = entradas[0]
    for i in range(1, n):
        atual = No(f"s{i}", "ADD", entradas=[atual, entradas[i]])
    motor = Motor(entradas)
    perturbacoes = {no.nome: 1e-6 for no in entradas}
    return motor, atual, perturbacoes, 2 * n - 1, 2 * n - 2


def medir(n):
    motor, saida, perturbacoes, quantidade_nos, quantidade_arestas = construir_cadeia(n)
    for _ in range(AQUECIMENTO):
        motor.analisar_perturbacoes(saida, perturbacoes)

    tempos_ms = []
    for _ in range(REPETICOES):
        inicio = time.perf_counter_ns()
        motor.analisar_perturbacoes(saida, perturbacoes)
        fim = time.perf_counter_ns()
        tempos_ms.append((fim - inicio) / 1e6)

    return {
        "entradas": n,
        "nos": quantidade_nos,
        "arestas": quantidade_arestas,
        "repeticoes": REPETICOES,
        "mediana_ms": statistics.median(tempos_ms),
        "media_ms": statistics.fmean(tempos_ms),
        "p25_ms": statistics.quantiles(tempos_ms, n=4, method="inclusive")[0],
        "p75_ms": statistics.quantiles(tempos_ms, n=4, method="inclusive")[2],
    }


def main():
    resultados = [medir(n) for n in TAMANHOS]
    with SAIDA.open("w", newline="", encoding="utf-8-sig") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=list(resultados[0]))
        escritor.writeheader()
        escritor.writerows(resultados)

    print("Python:", sys.version.replace("\n", " "))
    print("Plataforma:", platform.platform())
    print("Processador:", platform.processor() or "não informado pelo sistema")
    print("Aquecimento:", AQUECIMENTO, "| repetições por tamanho:", REPETICOES)
    print("Arquivo:", SAIDA)
    print("\n n | V | E | mediana (ms) | P25-P75 (ms)")
    for r in resultados:
        print(f"{r['entradas']:3d} | {r['nos']:3d} | {r['arestas']:3d} | {r['mediana_ms']:12.6f} | {r['p25_ms']:.6f}-{r['p75_ms']:.6f}")


if __name__ == "__main__":
    main()
