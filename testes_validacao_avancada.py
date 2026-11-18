
import math
import random
import statistics
import unittest

from motor import Motor, No
from casos import CASOS


# ============================================================
# CONFIGURAÇÕES
# ============================================================

TOLERANCIA = 1e-7

PASSO_DERIVADA = 1e-5

N_SIMULACOES = 10000

SEMENTE = 20261107


# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================

def criar_grafo_linear():
    """
    Cria o grafo:

        x ---- MUL ----
        2 ----/        \
                       ADD ---- saída
        3 --------------/

    Função matemática: f(x) = 2x + 3
    Valor nominal: f(5) = 13
    Sensibilidade em relação a x: 2
    """

    x = No("x", "INPUT", valor=5.0)
    dois = No("dois", "INPUT", valor=2.0)
    tres = No("tres", "INPUT", valor=3.0)

    dobro = No("dobro", "MUL", entradas=[x, dois])

    saida = No(
        "saida",
        "ADD",
        entradas=[dobro, tres]
    )

    return Motor([x, dois, tres, dobro, saida]), saida


# ============================================================
# 1. DERIVADAS ANALÍTICAS VERSUS DIFERENÇAS FINITAS
# ============================================================

class TestesDerivadasNumericas(unittest.TestCase):

    def test_derivadas_analiticas_versus_numericas(self):
        """
        Compara:

        Derivada analítica:
            calculada pelo método do motor.

        Derivada numérica:
            aproximação por diferenças finitas centrais.

        f'(x) ~= [f(x+h) - f(x-h)] / 2h
        """

        for construtor in CASOS:

            caso = construtor()

            motor = Motor(caso["nos"])

            sensibilidades = motor.calcular_sensibilidades(
                caso["saida"]
            )

            entradas = [
                no for no in caso["nos"]
                if no.operacao == "INPUT"
            ]

            for entrada in entradas:

                nome = entrada.nome

                with self.subTest(
                    caso=caso["nome"],
                    entrada=nome
                ):

                    h = PASSO_DERIVADA

                    # Avaliação com x + h
                    caso_mais = construtor()

                    motor_mais = Motor(caso_mais["nos"])

                    valor_mais = motor_mais.avaliar(
                        caso_mais["saida"],
                        {nome: h}
                    )

                    # Avaliação com x - h
                    caso_menos = construtor()

                    motor_menos = Motor(caso_menos["nos"])

                    valor_menos = motor_menos.avaliar(
                        caso_menos["saida"],
                        {nome: -h}
                    )

                    # Diferença finita central
                    derivada_numerica = (
                        valor_mais - valor_menos
                    ) / (2 * h)

                    derivada_analitica = sensibilidades[nome]

                    self.assertTrue(
                        math.isfinite(derivada_numerica),
                        "Derivada numérica não finita."
                    )

                    self.assertTrue(
                        math.isfinite(derivada_analitica),
                        "Derivada analítica não finita."
                    )

                    self.assertAlmostEqual(
                        derivada_analitica,
                        derivada_numerica,
                        delta=1e-5
                    )


# ============================================================
# 2. VALIDAÇÃO DE GRAFO MAIOR
# ============================================================

class TestesGrafosMaiores(unittest.TestCase):

    def criar_grafo_complexo(self):
        """
        Grafo:

             a ---- ADD ----\
             b ----/         \
                             MUL ----\
             a ---- MUL ----/        \
             b ----/                  ADD ---- saída
                                      /
             c ---- ADD -------------/
             d ----/

        Expressão:

        saída = ((a+b) * (a*b)) + (c+d)

        Valores:
            a = 2
            b = 3
            c = 4
            d = 5

        Resultado esperado:
            saída = 39
        """

        a = No("a", "INPUT", valor=2.0)
        b = No("b", "INPUT", valor=3.0)
        c = No("c", "INPUT", valor=4.0)
        d = No("d", "INPUT", valor=5.0)

        soma_ab = No(
            "soma_ab",
            "ADD",
            entradas=[a, b]
        )

        produto_ab = No(
            "produto_ab",
            "MUL",
            entradas=[a, b]
        )

        produto = No(
            "produto",
            "MUL",
            entradas=[soma_ab, produto_ab]
        )

        soma_cd = No(
            "soma_cd",
            "ADD",
            entradas=[c, d]
        )

        saida = No(
            "saida",
            "ADD",
            entradas=[produto, soma_cd]
        )

        nos = [
            a, b, c, d,
            soma_ab,
            produto_ab,
            produto,
            soma_cd,
            saida
        ]

        return Motor(nos), saida

    def test_avaliacao_de_grafo_maior(self):

        motor, saida = self.criar_grafo_complexo()

        resultado = motor.avaliar(saida)

        self.assertAlmostEqual(
            resultado,
            39.0,
            delta=TOLERANCIA
        )

    def test_sensibilidades_de_grafo_maior(self):

        motor, saida = self.criar_grafo_complexo()

        sensibilidades = motor.calcular_sensibilidades(
            saida
        )

        esperadas = {
            "a": 21.0,
            "b": 16.0,
            "c": 1.0,
            "d": 1.0
        }

        for nome, esperado in esperadas.items():

            with self.subTest(entrada=nome):

                self.assertIn(nome, sensibilidades)

                self.assertAlmostEqual(
                    sensibilidades[nome],
                    esperado,
                    delta=TOLERANCIA
                )

    def test_perturbacoes_em_multiplas_entradas(self):

        motor, saida = self.criar_grafo_complexo()

        perturbacoes = {
            "a": 0.1,
            "b": -0.1,
            "c": 0.2,
            "d": -0.2
        }

        resultado = motor.analisar_perturbacoes(
            saida,
            perturbacoes
        )

        self.assertAlmostEqual(
            resultado["saida_nominal"],
            39.0,
            delta=TOLERANCIA
        )

        self.assertTrue(
            math.isfinite(resultado["saida_perturbada"])
        )

        self.assertAlmostEqual(
            resultado["variacao_real"],
            (
                resultado["saida_perturbada"]
                - resultado["saida_nominal"]
            ),
            delta=TOLERANCIA
        )


# ============================================================
# 3. CASOS EXTREMOS
# ============================================================

class TestesCasosExtremos(unittest.TestCase):

    def test_operacoes_com_valores_negativos(self):

        a = No("a", "INPUT", valor=-2.0)
        b = No("b", "INPUT", valor=3.0)
        c = No("c", "INPUT", valor=-4.0)

        soma = No(
            "soma",
            "ADD",
            entradas=[a, b]
        )

        saida = No(
            "saida",
            "MUL",
            entradas=[soma, c]
        )

        motor = Motor([a, b, c, soma, saida])

        resultado = motor.avaliar(saida)

        self.assertAlmostEqual(
            resultado,
            -4.0,
            delta=TOLERANCIA
        )

    def test_multiplicacao_por_zero(self):

        a = No("a", "INPUT", valor=0.0)
        b = No("b", "INPUT", valor=-100.0)

        saida = No(
            "saida",
            "MUL",
            entradas=[a, b]
        )

        motor = Motor([a, b, saida])

        resultado = motor.avaliar(saida)

        self.assertAlmostEqual(
            resultado,
            0.0,
            delta=TOLERANCIA
        )

    def test_divisao_com_numerador_zero(self):

        a = No("a", "INPUT", valor=0.0)
        b = No("b", "INPUT", valor=5.0)

        saida = No(
            "saida",
            "DIV",
            entradas=[a, b]
        )

        motor = Motor([a, b, saida])

        resultado = motor.avaliar(saida)

        self.assertAlmostEqual(
            resultado,
            0.0,
            delta=TOLERANCIA
        )

    def test_denominador_proximo_de_zero(self):

        a = No("a", "INPUT", valor=10.0)
        b = No("b", "INPUT", valor=1e-8)

        saida = No(
            "saida",
            "DIV",
            entradas=[a, b]
        )

        motor = Motor([a, b, saida])

        resultado = motor.avaliar(saida)

        self.assertTrue(math.isfinite(resultado))

        self.assertAlmostEqual(
            resultado,
            1e9,
            delta=1.0
        )

    def test_resultado_com_entradas_muito_pequenas(self):

        a = No("a", "INPUT", valor=1e-8)
        b = No("b", "INPUT", valor=2e-8)

        saida = No(
            "saida",
            "ADD",
            entradas=[a, b]
        )

        motor = Motor([a, b, saida])

        resultado = motor.avaliar(saida)

        self.assertAlmostEqual(
            resultado,
            3e-8,
            delta=1e-15
        )


# ============================================================
# 4. VALIDAÇÃO ESTATÍSTICA DO MONTE CARLO
# ============================================================

class TestesEstatisticosMonteCarlo(unittest.TestCase):

    def test_media_empirica_proxima_da_media_teorica(self):
        """
        Função:

            f(x) = 2x + 3

        Entrada nominal:

            x = 5

        Perturbação:

            delta ~ Uniforme(-0.5, 0.5)

        Como a distribuição é simétrica:

            E[f(x + delta)] = 13

        A média amostral deve ficar próxima de 13.
        """

        gerador = random.Random(SEMENTE)

        amostras = []

        for _ in range(N_SIMULACOES):

            delta = gerador.uniform(-0.5, 0.5)

            motor, saida = criar_grafo_linear()

            resultado = motor.avaliar(
                saida,
                {"x": delta}
            )

            amostras.append(resultado)

        media_empirica = statistics.fmean(amostras)

        media_teorica = 13.0

        self.assertAlmostEqual(
            media_empirica,
            media_teorica,
            delta=0.03
        )

    def test_variancia_empirica_proxima_da_teorica(self):
        """
        Para:

            f(x) = 2x + 3

        e:

            delta ~ Uniforme(-0.5, 0.5)

        A variância de uma uniforme U(-a,a) é:

            Var(delta) = a² / 3

        Como a sensibilidade é 2:

            Var(f) = 2² * (0.5² / 3)

            Var(f) = 1/3
        """

        gerador = random.Random(SEMENTE)

        amostras = []

        for _ in range(N_SIMULACOES):

            delta = gerador.uniform(-0.5, 0.5)

            motor, saida = criar_grafo_linear()

            resultado = motor.avaliar(
                saida,
                {"x": delta}
            )

            amostras.append(resultado)

        variancia_empirica = statistics.pvariance(amostras)

        variancia_teorica = 1.0 / 3.0

        self.assertAlmostEqual(
            variancia_empirica,
            variancia_teorica,
            delta=0.025
        )

    def test_reprodutibilidade_das_amostras(self):

        def executar_amostras(semente):

            gerador = random.Random(semente)

            resultados = []

            for _ in range(100):

                delta = gerador.uniform(-0.5, 0.5)

                motor, saida = criar_grafo_linear()

                resultado = motor.avaliar(
                    saida,
                    {"x": delta}
                )

                resultados.append(resultado)

            return resultados

        primeira_execucao = executar_amostras(SEMENTE)

        segunda_execucao = executar_amostras(SEMENTE)

        self.assertEqual(
            primeira_execucao,
            segunda_execucao
        )


# ============================================================
# EXECUÇÃO
# ============================================================

if __name__ == "__main__":

    unittest.main(verbosity=2)
