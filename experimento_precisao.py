
import csv
import math
import random
import statistics
from pathlib import Path

import matplotlib.pyplot as plt

from motor import Motor, No


# ============================================================
# CONFIGURAÇÕES DO EXPERIMENTO
# ============================================================

DIRETORIO = Path(__file__).resolve().parent

# Quantidade de entradas por grafo.
# Deve ser par, pois as entradas serão agrupadas em pares.
TAMANHOS_GRAFO = [4, 8, 16, 32]

# Intensidades das perturbações absolutas.
INTENSIDADES = [0.001, 0.01, 0.05, 0.10]

# Número de simulações para cada combinação.
N_SIMULACOES = 1000

# Semente para garantir reprodutibilidade.
SEMENTE = 20261107

# Arquivos de saída.
ARQUIVO_AMOSTRAS = DIRETORIO / "experimento_amostras.csv"
ARQUIVO_RESUMO = DIRETORIO / "experimento_resumo.csv"

GRAFICO_MAE = DIRETORIO / "grafico_erro_absoluto.png"
GRAFICO_RMSE = DIRETORIO / "grafico_rmse.png"
GRAFICO_COMPARACAO = DIRETORIO / "grafico_real_vs_linear.png"


# ============================================================
# 1. CONSTRUÇÃO DOS GRAFOS
# ============================================================

def criar_grafo(tamanho):
    """
    Constrói um grafo aritmético com tamanho configurável.

    Estrutura:

        x0 ----\
               MUL ----\
        x1 ----/        \
                        ADD ----\
        x2 ----\        /        \
               MUL ----          ADD ---- saída
        x3 ----/                 /
                                /
        ...

    Expressão geral:

        f(x) = x0*x1 + x2*x3 + ... + xn-2*xn-1

    Características:
        - Entradas independentes.
        - Ramificações.
        - Operações de multiplicação.
        - Convergência por adição.
        - Não linearidade de segunda ordem.

    O tamanho informado representa a quantidade de entradas.
    """

    if tamanho < 4 or tamanho % 2 != 0:
        raise ValueError(
            "O tamanho do grafo deve ser par e maior ou igual a 4."
        )

    nos = []
    entradas = []

    # Criação das entradas.
    for i in range(tamanho):

        valor = 1.0 + (i % 5) * 0.1

        entrada = No(
            f"x{i}",
            "INPUT",
            valor=valor
        )

        entradas.append(entrada)
        nos.append(entrada)

    # Criação dos produtos.
    produtos = []

    for i in range(0, tamanho, 2):

        produto = No(
            f"produto_{i // 2}",
            "MUL",
            entradas=[
                entradas[i],
                entradas[i + 1]
            ]
        )

        produtos.append(produto)
        nos.append(produto)

    # Convergência dos ramos por adição.
    saida_atual = produtos[0]

    for i in range(1, len(produtos)):

        soma = No(
            f"soma_{i}",
            "ADD",
            entradas=[
                saida_atual,
                produtos[i]
            ]
        )

        nos.append(soma)
        saida_atual = soma

    motor = Motor(nos)

    return motor, saida_atual, entradas


# ============================================================
# 2. EXECUÇÃO DE UMA SIMULAÇÃO
# ============================================================

def executar_simulacao(tamanho, intensidade, gerador):
    """
    Executa uma simulação independente.

    Cada entrada recebe uma perturbação aleatória
    uniforme no intervalo [-intensidade, +intensidade].

    Retorna:
        - saída nominal;
        - saída perturbada;
        - variação real;
        - variação linear estimada;
        - resíduo da aproximação.
    """

    motor, saida, entradas = criar_grafo(tamanho)

    perturbacoes = {}

    for entrada in entradas:

        delta = gerador.uniform(
            -intensidade,
            intensidade
        )

        perturbacoes[entrada.nome] = delta

    resultado = motor.analisar_perturbacoes(
        saida,
        perturbacoes
    )

    variacao_real = resultado["variacao_real"]

    variacao_linear = resultado["variacao_linear_estimada"]

    residuo = variacao_real - variacao_linear

    return {
        "saida_nominal": resultado["saida_nominal"],
        "saida_perturbada": resultado["saida_perturbada"],
        "variacao_real": variacao_real,
        "variacao_linear": variacao_linear,
        "residuo": residuo,
        "erro_absoluto": abs(residuo),
        "erro_quadratico": residuo ** 2,
        "erro_normalizado": (
            abs(residuo) / max(
                abs(resultado["saida_nominal"]),
                1e-15
            )
        )
    }


# ============================================================
# 3. MÉTRICAS ESTATÍSTICAS
# ============================================================

def calcular_percentil(valores, percentil):

    ordenados = sorted(valores)

    if not ordenados:
        return 0.0

    indice = math.ceil(
        (percentil / 100) * len(ordenados)
    ) - 1

    indice = max(
        0,
        min(indice, len(ordenados) - 1)
    )

    return ordenados[indice]


def calcular_correlacao(valores_x, valores_y):

    media_x = statistics.fmean(valores_x)
    media_y = statistics.fmean(valores_y)

    numerador = sum(
        (x - media_x) * (y - media_y)
        for x, y in zip(valores_x, valores_y)
    )

    soma_x = sum(
        (x - media_x) ** 2
        for x in valores_x
    )

    soma_y = sum(
        (y - media_y) ** 2
        for y in valores_y
    )

    denominador = math.sqrt(soma_x * soma_y)

    if denominador == 0:
        return None

    return numerador / denominador


def calcular_metricas(amostras):
    """
    Calcula métricas de comparação entre
    variação real e aproximação linear.
    """

    reais = [
        amostra["variacao_real"]
        for amostra in amostras
    ]

    lineares = [
        amostra["variacao_linear"]
        for amostra in amostras
    ]

    residuos = [
        amostra["residuo"]
        for amostra in amostras
    ]

    erros = [
        abs(residuo)
        for residuo in residuos
    ]

    erros_quadraticos = [
        residuo ** 2
        for residuo in residuos
    ]

    saidas_nominais = [
        amostra["saida_nominal"]
        for amostra in amostras
    ]

    mae = statistics.fmean(erros)

    mse = statistics.fmean(erros_quadraticos)

    rmse = math.sqrt(mse)

    media_real = statistics.fmean(reais)

    media_linear = statistics.fmean(lineares)

    media_modulo_real = statistics.fmean(
        abs(valor) for valor in reais
    )

    vies = statistics.fmean(residuos)

    saida_nominal_media = statistics.fmean(
        saidas_nominais
    )

    nrmse = (
        rmse / abs(saida_nominal_media)
        if saida_nominal_media != 0
        else None
    )

    erro_relativo_medio = (
        mae / media_modulo_real
        if media_modulo_real > 1e-15
        else None
    )

    correlacao = calcular_correlacao(
        reais,
        lineares
    )

    return {
        "quantidade_amostras": len(amostras),
        "media_variacao_real": media_real,
        "media_variacao_linear": media_linear,
        "media_modulo_variacao_real": media_modulo_real,
        "mae": mae,
        "mse": mse,
        "rmse": rmse,
        "vies": vies,
        "nrmse": nrmse,
        "erro_relativo_medio": erro_relativo_medio,
        "mediana_erro_absoluto": statistics.median(erros),
        "percentil_95_erro": calcular_percentil(erros, 95),
        "correlacao": correlacao
    }


# ============================================================
# 4. EXECUÇÃO COMPLETA DO EXPERIMENTO
# ============================================================

def executar_experimento():

    gerador = random.Random(SEMENTE)

    todas_amostras = []
    todos_resumos = []

    total_combinacoes = (
        len(TAMANHOS_GRAFO) * len(INTENSIDADES)
    )

    combinacao_atual = 0

    print("=" * 65)
    print("EXPERIMENTO DE PRECISÃO DA APROXIMAÇÃO LINEAR")
    print("=" * 65)

    print(f"Simulações por combinação: {N_SIMULACOES}")
    print(f"Tamanhos de grafo: {TAMANHOS_GRAFO}")
    print(f"Intensidades: {INTENSIDADES}")
    print(f"Semente: {SEMENTE}")
    print()

    for tamanho in TAMANHOS_GRAFO:

        for intensidade in INTENSIDADES:

            combinacao_atual += 1

            print(
                f"[{combinacao_atual}/{total_combinacoes}] "
                f"Grafo com {tamanho} entradas | "
                f"Perturbação: {intensidade}"
            )

            amostras_combinacao = []

            for simulacao in range(N_SIMULACOES):

                resultado = executar_simulacao(
                    tamanho,
                    intensidade,
                    gerador
                )

                amostra = {
                    "tamanho_entradas": tamanho,
                    "quantidade_nos": 2 * tamanho - 1,
                    "intensidade": intensidade,
                    "simulacao": simulacao + 1,
                    **resultado
                }

                amostras_combinacao.append(amostra)

                todas_amostras.append(amostra)

            metricas = calcular_metricas(
                amostras_combinacao
            )

            resumo = {
                "tamanho_entradas": tamanho,
                "quantidade_nos": 2 * tamanho - 1,
                "intensidade": intensidade,
                **metricas
            }

            todos_resumos.append(resumo)

            print(
                f"  MAE: {metricas['mae']:.10f} | "
                f"RMSE: {metricas['rmse']:.10f} | "
                f"NRMSE: {metricas['nrmse']:.10f}"
            )

    return todas_amostras, todos_resumos


# ============================================================
# 5. EXPORTAÇÃO DOS CSVs
# ============================================================

def exportar_csv(caminho, dados):

    if not dados:
        raise ValueError("Não existem dados para exportar.")

    campos = list(dados[0].keys())

    with open(
        caminho,
        "w",
        newline="",
        encoding="utf-8-sig"
    ) as arquivo:

        escritor = csv.DictWriter(
            arquivo,
            fieldnames=campos
        )

        escritor.writeheader()
        escritor.writerows(dados)

    print(f"Arquivo gerado: {caminho.name}")


# ============================================================
# 6. GRÁFICO DO ERRO ABSOLUTO MÉDIO
# ============================================================

def gerar_grafico_mae(resumos):

    plt.figure(figsize=(10, 6))

    for tamanho in TAMANHOS_GRAFO:

        dados = [
            resumo
            for resumo in resumos
            if resumo["tamanho_entradas"] == tamanho
        ]

        dados.sort(
            key=lambda item: item["intensidade"]
        )

        x = [
            item["intensidade"]
            for item in dados
        ]

        y = [
            item["mae"]
            for item in dados
        ]

        plt.plot(
            x,
            y,
            marker="o",
            label=f"{tamanho} entradas"
        )

    plt.title(
        "Erro absoluto médio da aproximação linear"
    )

    plt.xlabel("Intensidade da perturbação")
    plt.ylabel("MAE")

    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()

    plt.savefig(
        GRAFICO_MAE,
        dpi=300
    )

    plt.close()

    print(f"Gráfico gerado: {GRAFICO_MAE.name}")


# ============================================================
# 7. GRÁFICO RMSE
# ============================================================

def gerar_grafico_rmse(resumos):

    plt.figure(figsize=(10, 6))

    for tamanho in TAMANHOS_GRAFO:

        dados = [
            resumo
            for resumo in resumos
            if resumo["tamanho_entradas"] == tamanho
        ]

        dados.sort(
            key=lambda item: item["intensidade"]
        )

        x = [
            item["intensidade"]
            for item in dados
        ]

        y = [
            item["rmse"]
            for item in dados
        ]

        plt.plot(
            x,
            y,
            marker="o",
            label=f"{tamanho} entradas"
        )

    plt.title(
        "Raiz do erro quadrático médio (RMSE)"
    )

    plt.xlabel("Intensidade da perturbação")
    plt.ylabel("RMSE")

    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()

    plt.savefig(
        GRAFICO_RMSE,
        dpi=300
    )

    plt.close()

    print(f"Gráfico gerado: {GRAFICO_RMSE.name}")


# ============================================================
# 8. GRÁFICO VARIAÇÃO REAL VERSUS LINEAR
# ============================================================

def gerar_grafico_comparacao(amostras):

    plt.figure(figsize=(10, 7))

    # Limita a quantidade de pontos exibidos por
    # combinação para manter o gráfico legível.
    for tamanho in TAMANHOS_GRAFO:

        for intensidade in INTENSIDADES:

            dados = [
                amostra
                for amostra in amostras
                if (
                    amostra["tamanho_entradas"] == tamanho
                    and amostra["intensidade"] == intensidade
                )
            ]

            # Exibe até 150 pontos por combinação.
            passo = max(
                1,
                len(dados) // 150
            )

            dados = dados[::passo]

            x = [
                item["variacao_real"]
                for item in dados
            ]

            y = [
                item["variacao_linear"]
                for item in dados
            ]

            plt.scatter(
                x,
                y,
                alpha=0.25,
                s=12,
                label=f"{tamanho} entradas, delta={intensidade}"
            )

    valores = [
        valor
        for amostra in amostras
        for valor in (
            amostra["variacao_real"],
            amostra["variacao_linear"]
        )
    ]

    minimo = min(valores)
    maximo = max(valores)

    margem = (maximo - minimo) * 0.05

    plt.plot(
        [minimo - margem, maximo + margem],
        [minimo - margem, maximo + margem],
        linestyle="--",
        label="Correspondência ideal"
    )

    plt.title(
        "Variação real versus aproximação linear"
    )

    plt.xlabel("Variação real")
    plt.ylabel("Variação linear estimada")

    plt.legend(
        fontsize=8,
        loc="best"
    )

    plt.grid(True, alpha=0.3)
    plt.tight_layout()

    plt.savefig(
        GRAFICO_COMPARACAO,
        dpi=300
    )

    plt.close()

    print(
        f"Gráfico gerado: {GRAFICO_COMPARACAO.name}"
    )


# ============================================================
# 9. RELATÓRIO FINAL
# ============================================================

def exibir_resumo(resumos):

    print()
    print("=" * 90)
    print("RESUMO DOS RESULTADOS")
    print("=" * 90)

    cabecalho = (
        f"{'Entradas':>10} "
        f"{'Nós':>8} "
        f"{'Delta':>10} "
        f"{'MAE':>15} "
        f"{'RMSE':>15} "
        f"{'NRMSE':>12}"
    )

    print(cabecalho)
    print("-" * 90)

    for item in resumos:

        print(
            f"{item['tamanho_entradas']:>10} "
            f"{item['quantidade_nos']:>8} "
            f"{item['intensidade']:>10.4f} "
            f"{item['mae']:>15.8f} "
            f"{item['rmse']:>15.8f} "
            f"{item['nrmse']:>12.8f}"
        )

    print("=" * 90)


# ============================================================
# 10. PROGRAMA PRINCIPAL
# ============================================================

def main():

    try:

        amostras, resumos = executar_experimento()

        exportar_csv(
            ARQUIVO_AMOSTRAS,
            amostras
        )

        exportar_csv(
            ARQUIVO_RESUMO,
            resumos
        )

        gerar_grafico_mae(resumos)

        gerar_grafico_rmse(resumos)

        gerar_grafico_comparacao(amostras)

        exibir_resumo(resumos)

        print()
        print("=" * 65)
        print("EXPERIMENTO CONCLUÍDO COM SUCESSO")
        print("=" * 65)

        print(
            f"Total de amostras: {len(amostras)}"
        )

        print(
            f"Total de combinações: {len(resumos)}"
        )

        print(
            f"Resultados salvos em: {DIRETORIO}"
        )

    except Exception as erro:

        print()
        print("ERRO DURANTE O EXPERIMENTO:")
        print(erro)

        raise


if __name__ == "__main__":
    main()
