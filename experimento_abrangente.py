
"""
EXPERIMENTO ABRANGENTE
Análise da precisão da aproximação linear em grafos computacionais.

Operações: ADD, SUB, MUL, DIV
Estruturas: cadeia e ramificada
Perturbações: positivas, negativas e combinadas

Arquivos gerados:
- abrangente_amostras.csv
- abrangente_resumo.csv
- abrangente_intervalos.csv
- grafico_operacoes.png
- grafico_estruturas.png
- grafico_perturbacoes.png
- grafico_real_linear.png

Não modifica os arquivos existentes do projeto.
"""

import csv
import math
import random
import statistics
from pathlib import Path

import matplotlib.pyplot as plt

from motor import Motor, No


# ============================================================
# CONFIGURAÇÕES
# ============================================================

PASTA = Path(__file__).resolve().parent

TAMANHOS = [4, 8, 16, 32]
INTENSIDADES = [0.001, 0.01, 0.05, 0.10]

SIMULACOES = 1000
SEMENTE = 20261107

OPERACOES = ["ADD", "SUB", "MUL", "DIV"]
ESTRUTURAS = ["cadeia", "ramificada"]
TIPOS_PERTURBACAO = ["positiva", "negativa", "combinada"]

random.seed(SEMENTE)


# ============================================================
# CONSTRUÇÃO DOS GRAFOS
# ============================================================

def criar_entrada(nome, valor):
    return No(nome, "INPUT", valor=valor)


def aplicar_operacao(nome, operacao, a, b):
    return No(
        nome,
        operacao,
        entradas=[a, b]
    )


def criar_grafo(quantidade, operacao, estrutura):

    entradas = [
        criar_entrada(
            f"x{i}",
            2.0 + (i % 5) * 0.2
        )
        for i in range(quantidade)
    ]

    contador = 0

    if estrutura == "cadeia":

        atual = entradas[0]

        for i in range(1, quantidade):

            atual = aplicar_operacao(
                f"op{contador}",
                operacao,
                atual,
                entradas[i]
            )

            contador += 1

    elif estrutura == "ramificada":

        camada = entradas[:]

        while len(camada) > 1:

            proxima = []

            for i in range(0, len(camada), 2):

                if i + 1 < len(camada):

                    no = aplicar_operacao(
                        f"op{contador}",
                        operacao,
                        camada[i],
                        camada[i + 1]
                    )

                    proxima.append(no)
                    contador += 1

                else:
                    proxima.append(camada[i])

            camada = proxima

        atual = camada[0]

    else:
        raise ValueError(
            f"Estrutura desconhecida: {estrutura}"
        )

    motor = Motor(nos=entradas)

    return motor, entradas, atual


# ============================================================
# GERAÇÃO DAS PERTURBAÇÕES
# ============================================================

def gerar_perturbacoes(entradas, intensidade, tipo):

    perturbacoes = {}

    for no in entradas:

        magnitude = random.uniform(0.5, 1.0)

        if tipo == "positiva":
            sinal = 1

        elif tipo == "negativa":
            sinal = -1

        elif tipo == "combinada":
            sinal = random.choice([-1, 1])

        else:
            raise ValueError(
                f"Tipo de perturbação desconhecido: {tipo}"
            )

        perturbacoes[no.nome] = (
            no.valor * intensidade * magnitude * sinal
        )

    return perturbacoes


# ============================================================
# MÉTRICAS
# ============================================================

def percentil(valores, percentual):

    ordenados = sorted(valores)

    indice = math.ceil(
        percentual * len(ordenados)
    ) - 1

    indice = max(
        0,
        min(indice, len(ordenados) - 1)
    )

    return ordenados[indice]


def calcular_metricas(reais, estimados):

    # Convencao unica do projeto: residuo = variacao_real - variacao_linear.
    residuos = [
        real - estimado
        for real, estimado in zip(reais, estimados)
    ]

    erros_absolutos = [
        abs(residuo) for residuo in residuos
    ]

    mae = statistics.mean(erros_absolutos)

    mse = statistics.mean(
        residuo ** 2 for residuo in residuos
    )

    rmse = math.sqrt(mse)

    # NRMSE normalizado pela amplitude das variações reais.
    amplitude = max(reais) - min(reais)

    nrmse = (
        rmse / amplitude
        if amplitude > 1e-12
        else float("nan")
    )

    vies = statistics.mean(residuos)

    p95 = percentil(
        erros_absolutos,
        0.95
    )

    # MAPE: desconsidera valores reais próximos de zero.
    percentuais = [
        abs(estimado - real) / abs(real) * 100
        for real, estimado in zip(reais, estimados)
        if abs(real) > 1e-12
    ]

    mape = (
        statistics.mean(percentuais)
        if percentuais
        else float("nan")
    )

    if (
        len(reais) > 1
        and statistics.stdev(reais) > 0
        and statistics.stdev(estimados) > 0
    ):
        correlacao = statistics.correlation(
            reais,
            estimados
        )
    else:
        correlacao = float("nan")

    return {
        "MAE": mae,
        "MSE": mse,
        "RMSE": rmse,
        "NRMSE": nrmse,
        "MAPE": mape,
        "Vies": vies,
        "P95": p95,
        "Correlacao": correlacao
    }


# ============================================================
# INTERVALO DE CONFIANÇA
# ============================================================

def intervalo_confianca(valores):

    media = statistics.mean(valores)

    if len(valores) < 2:
        return media, media

    desvio = statistics.stdev(valores)

    erro_padrao = (
        desvio / math.sqrt(len(valores))
    )

    margem = 1.96 * erro_padrao

    return (
        media - margem,
        media + margem
    )


# ============================================================
# EXPORTAÇÃO CSV
# ============================================================

def salvar_csv(nome, dados):

    if not dados:
        print(
            f"AVISO: nenhum dado para salvar em {nome}"
        )
        return

    caminho = PASTA / nome

    with open(
        caminho,
        "w",
        newline="",
        encoding="utf-8-sig"
    ) as arquivo:

        escritor = csv.DictWriter(
            arquivo,
            fieldnames=list(dados[0].keys()),
            delimiter=";"
        )

        escritor.writeheader()
        escritor.writerows(dados)

    print("Arquivo gerado:", caminho)


# ============================================================
# GRÁFICOS
# ============================================================

def gerar_graficos(resumos, amostras):

    if not resumos:
        return

    # --------------------------------------------------------
    # 1. Comparação entre operações
    # --------------------------------------------------------

    plt.figure(figsize=(11, 6))

    for operacao in OPERACOES:

        x = []
        y = []

        for intensidade in INTENSIDADES:

            valores = [
                r["RMSE"]
                for r in resumos
                if r["operacao"] == operacao
                and r["intensidade"] == intensidade
                and math.isfinite(r["RMSE"])
            ]

            if valores:
                x.append(intensidade * 100)
                y.append(statistics.mean(valores))

        if x:
            plt.plot(
                x,
                y,
                marker="o",
                label=operacao
            )

    plt.xlabel("Intensidade da perturbação (%)")
    plt.ylabel("RMSE médio")
    plt.title("Influência das operações matemáticas")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()

    plt.savefig(
        PASTA / "grafico_operacoes.png",
        dpi=200
    )

    plt.close()

    # --------------------------------------------------------
    # 2. Comparação entre estruturas
    # --------------------------------------------------------

    plt.figure(figsize=(11, 6))

    for estrutura in ESTRUTURAS:

        x = []
        y = []

        for tamanho in TAMANHOS:

            valores = [
                r["RMSE"]
                for r in resumos
                if r["estrutura"] == estrutura
                and r["entradas"] == tamanho
                and math.isfinite(r["RMSE"])
            ]

            if valores:
                x.append(tamanho)
                y.append(statistics.mean(valores))

        if x:
            plt.plot(
                x,
                y,
                marker="o",
                label=estrutura
            )

    plt.xlabel("Quantidade de entradas")
    plt.ylabel("RMSE médio")
    plt.title("Influência da estrutura e do tamanho")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()

    plt.savefig(
        PASTA / "grafico_estruturas.png",
        dpi=200
    )

    plt.close()

    # --------------------------------------------------------
    # 3. Comparação entre tipos de perturbação
    # --------------------------------------------------------

    plt.figure(figsize=(11, 6))

    for tipo in TIPOS_PERTURBACAO:

        x = []
        y = []

        for intensidade in INTENSIDADES:

            valores = [
                r["RMSE"]
                for r in resumos
                if r["tipo_perturbacao"] == tipo
                and r["intensidade"] == intensidade
                and math.isfinite(r["RMSE"])
            ]

            if valores:
                x.append(intensidade * 100)
                y.append(statistics.mean(valores))

        if x:
            plt.plot(
                x,
                y,
                marker="o",
                label=tipo
            )

    plt.xlabel("Intensidade da perturbação (%)")
    plt.ylabel("RMSE médio")
    plt.title("Influência do sentido da perturbação")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()

    plt.savefig(
        PASTA / "grafico_perturbacoes.png",
        dpi=200
    )

    plt.close()

    # --------------------------------------------------------
    # 4. Variação real versus estimada
    # --------------------------------------------------------

    quantidade = min(
        5000,
        len(amostras)
    )

    selecionadas = amostras[:quantidade]

    reais = [
        a["variacao_real"]
        for a in selecionadas
    ]

    lineares = [
        a["variacao_linear"]
        for a in selecionadas
    ]

    plt.figure(figsize=(8, 8))

    plt.scatter(
        reais,
        lineares,
        alpha=0.25
    )

    minimo = min(reais + lineares)
    maximo = max(reais + lineares)

    plt.plot(
        [minimo, maximo],
        [minimo, maximo],
        linestyle="--",
        label="Correspondência perfeita"
    )

    plt.xlabel("Variação real")
    plt.ylabel("Variação estimada")
    plt.title("Variação real versus aproximação linear")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()

    plt.savefig(
        PASTA / "grafico_real_linear.png",
        dpi=200
    )

    plt.close()

    print("Todos os gráficos foram gerados.")


# ============================================================
# EXECUÇÃO DO EXPERIMENTO
# ============================================================

def executar():

    amostras = []
    resumos = []
    intervalos = []

    total = (
        len(TAMANHOS)
        * len(INTENSIDADES)
        * len(OPERACOES)
        * len(ESTRUTURAS)
        * len(TIPOS_PERTURBACAO)
    )

    combinacao = 0

    print("=" * 75)
    print("EXPERIMENTO ABRANGENTE DE PROPAGAÇÃO DE ERROS")
    print("=" * 75)

    print("Simulações por combinação:", SIMULACOES)
    print("Combinações previstas:", total)
    print("Amostras previstas:", total * SIMULACOES)
    print("Semente:", SEMENTE)

    for tamanho in TAMANHOS:

        for operacao in OPERACOES:

            for estrutura in ESTRUTURAS:

                motor, entradas, saida = criar_grafo(
                    tamanho,
                    operacao,
                    estrutura
                )

                try:
                    nominal = motor.avaliar(saida)

                except Exception as erro:
                    raise RuntimeError(
                        f"Erro na avaliação nominal: "
                        f"{operacao}, {estrutura}, "
                        f"{tamanho} entradas: {erro}"
                    ) from erro

                if not math.isfinite(nominal):
                    raise ValueError(
                        "A saída nominal não é finita."
                    )

                for intensidade in INTENSIDADES:

                    for tipo in TIPOS_PERTURBACAO:

                        combinacao += 1

                        reais = []
                        estimados = []
                        erros_absolutos = []

                        print(
                            f"\n[{combinacao}/{total}] "
                            f"{operacao} | {estrutura} | "
                            f"{tamanho} entradas | "
                            f"delta={intensidade} | {tipo}"
                        )

                        for repeticao in range(SIMULACOES):

                            perturbacoes = gerar_perturbacoes(
                                entradas,
                                intensidade,
                                tipo
                            )

                            try:

                                resultado = motor.analisar_perturbacoes(
                                    saida,
                                    perturbacoes
                                )

                                real = resultado[
                                    "variacao_real"
                                ]

                                linear = resultado[
                                    "variacao_linear_estimada"
                                ]

                            except (ValueError, ZeroDivisionError):
                                # Registra a simulação inválida,
                                # sem interromper toda a execução.
                                continue

                            if not (
                                math.isfinite(real)
                                and math.isfinite(linear)
                            ):
                                continue

                            erro = abs(real - linear)

                            reais.append(real)
                            estimados.append(linear)
                            erros_absolutos.append(erro)

                            amostras.append({
                                "operacao": operacao,
                                "estrutura": estrutura,
                                "entradas": tamanho,
                                "intensidade": intensidade,
                                "tipo_perturbacao": tipo,
                                "repeticao": repeticao + 1,
                                "saida_nominal": nominal,
                                "variacao_real": real,
                                "variacao_linear": linear,
                                "erro_absoluto": erro,
                                # Mantem a mesma convencao de R definida na monografia.
                                "erro_assinado": real - linear
                            })

                        if not reais:
                            print(
                                "  Nenhuma simulação válida."
                            )
                            continue

                        metricas = calcular_metricas(
                            reais,
                            estimados
                        )

                        resumo = {
                            "operacao": operacao,
                            "estrutura": estrutura,
                            "entradas": tamanho,
                            "intensidade": intensidade,
                            "tipo_perturbacao": tipo,
                            "amostras_validas": len(reais),
                            "amostras_invalidas": (
                                SIMULACOES - len(reais)
                            ),
                            **metricas
                        }

                        resumos.append(resumo)

                        inferior, superior = intervalo_confianca(
                            erros_absolutos
                        )

                        intervalos.append({
                            "operacao": operacao,
                            "estrutura": estrutura,
                            "entradas": tamanho,
                            "intensidade": intensidade,
                            "tipo_perturbacao": tipo,
                            "MAE_IC95_inferior": inferior,
                            "MAE_IC95_superior": superior
                        })

                        print(
                            f"  Válidas: {len(reais)}/{SIMULACOES}"
                        )

                        print(
                            f"  MAE={metricas['MAE']:.8f} | "
                            f"RMSE={metricas['RMSE']:.8f} | "
                            f"NRMSE={metricas['NRMSE']:.8f}"
                        )

    # ========================================================
    # SALVAMENTO
    # ========================================================

    salvar_csv(
        "abrangente_amostras.csv",
        amostras
    )

    salvar_csv(
        "abrangente_resumo.csv",
        resumos
    )

    salvar_csv(
        "abrangente_intervalos.csv",
        intervalos
    )

    gerar_graficos(
        resumos,
        amostras
    )

    print("\n" + "=" * 75)
    print("EXPERIMENTO CONCLUÍDO")
    print("=" * 75)

    print("Total de amostras válidas:", len(amostras))
    print("Combinações com resultados:", len(resumos))
    print("Resultados salvos em:", PASTA)


# ============================================================
# INÍCIO
# ============================================================

if __name__ == "__main__":
    executar()
