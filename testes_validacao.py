
import csv
import math
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from motor import Motor, No
from casos import CASOS


# ============================================================
# CONFIGURAÇÕES
# ============================================================

DIRETORIO_PROJETO = Path(__file__).resolve().parent

ARQUIVOS_MONTE_CARLO = [
    "monte_carlo_amostras.csv",
    "monte_carlo_resumo.csv",
]

TOLERANCIA = 1e-9


# ============================================================
# TESTES DE VALIDAÇÃO DO MOTOR
# ============================================================

class TestesValidacaoMotor(unittest.TestCase):

    def setUp(self):
        self.casos = [construtor() for construtor in CASOS]

    # --------------------------------------------------------
    # 1. QUANTIDADE E IDENTIFICAÇÃO DOS CASOS
    # --------------------------------------------------------

    def test_quantidade_e_identificacao_dos_casos(self):
        self.assertEqual(len(self.casos), 4)

        for caso in self.casos:
            self.assertIn("nome", caso)
            self.assertIn("nos", caso)
            self.assertIn("saida", caso)
            self.assertIn("perturbacoes_teste", caso)

    # --------------------------------------------------------
    # 2. VALORES NOMINAIS
    # --------------------------------------------------------

    def test_valores_nominais(self):
        valores_esperados = [
            50.0,
            4.0,
            30.0,
            4.0,
        ]

        for caso, esperado in zip(self.casos, valores_esperados):
            with self.subTest(caso=caso["nome"]):
                motor = Motor(caso["nos"])

                resultado = motor.avaliar(caso["saida"])

                self.assertAlmostEqual(
                    resultado,
                    esperado,
                    delta=TOLERANCIA
                )

    # --------------------------------------------------------
    # 3. VALORES PERTURBADOS
    # --------------------------------------------------------

    def test_valores_perturbados(self):
        valores_esperados = [
            55.0,
            6.25,
            41.25,
            12.0 / 3.1,
        ]

        for caso, esperado in zip(self.casos, valores_esperados):
            with self.subTest(caso=caso["nome"]):
                motor = Motor(caso["nos"])

                resultado = motor.avaliar(
                    caso["saida"],
                    caso["perturbacoes_teste"]
                )

                self.assertAlmostEqual(
                    resultado,
                    esperado,
                    delta=TOLERANCIA
                )

    # --------------------------------------------------------
    # 4. SENSIBILIDADES ANALÍTICAS
    # --------------------------------------------------------

    def test_sensibilidades_analiticas(self):
        sensibilidades_esperadas = [
            {"a": 10.0, "b": 10.0, "c": 5.0, "soma": 10.0},
            {"a": 4.0},
            {"a": 21.0, "b": 16.0},
            {"a": 1.0 / 3.0, "b": -4.0 / 3.0},
        ]

        for caso, esperadas in zip(
            self.casos,
            sensibilidades_esperadas
        ):
            with self.subTest(caso=caso["nome"]):
                motor = Motor(caso["nos"])

                resultado = motor.calcular_sensibilidades(
                    caso["saida"]
                )

                for nome, esperado in esperadas.items():
                    self.assertIn(nome, resultado)

                    self.assertAlmostEqual(
                        resultado[nome],
                        esperado,
                        delta=TOLERANCIA
                    )

    # --------------------------------------------------------
    # 5. APROXIMAÇÃO LINEAR DE PRIMEIRA ORDEM
    # --------------------------------------------------------

    def test_aproximacao_linear_de_primeira_ordem(self):
        variacoes_esperadas = [
            5.0,
            2.0,
            10.5,
            -0.13333333333333333,
        ]

        for caso, esperado in zip(
            self.casos,
            variacoes_esperadas
        ):
            with self.subTest(caso=caso["nome"]):
                motor = Motor(caso["nos"])

                resultado = motor.estimar_variacao_linear(
                    caso["saida"],
                    caso["perturbacoes_teste"]
                )

                self.assertAlmostEqual(
                    resultado,
                    esperado,
                    delta=TOLERANCIA
                )

    # --------------------------------------------------------
    # 6. CONSISTÊNCIA DA VARIAÇÃO REAL
    # --------------------------------------------------------

    def test_consistencia_da_variacao_real(self):
        for caso in self.casos:
            with self.subTest(caso=caso["nome"]):
                motor = Motor(caso["nos"])

                resultado = motor.analisar_perturbacoes(
                    caso["saida"],
                    caso["perturbacoes_teste"]
                )

                variacao_calculada = (
                    resultado["saida_perturbada"]
                    - resultado["saida_nominal"]
                )

                self.assertAlmostEqual(
                    variacao_calculada,
                    resultado["variacao_real"],
                    delta=TOLERANCIA
                )

                self.assertAlmostEqual(
                    abs(variacao_calculada),
                    resultado["erro_absoluto_real"],
                    delta=TOLERANCIA
                )

    # --------------------------------------------------------
    # 7. DETECÇÃO DE CICLOS NO GRAFO
    # --------------------------------------------------------

    def test_detecta_ciclo_no_grafo(self):
        x = No(
            "x",
            "INPUT",
            valor=1.0
        )

        a = No(
            "a",
            "ADD",
            entradas=[]
        )

        b = No(
            "b",
            "ADD",
            entradas=[]
        )

        # Cria dependência circular:
        # a depende de b e b depende de a.
        a.entradas = [b, x]
        b.entradas = [a, x]

        motor = Motor([a, b, x])

        with self.assertRaises(ValueError):
            motor.avaliar(a)

    # --------------------------------------------------------
    # 8. DIVISÃO POR ZERO
    # --------------------------------------------------------

    def test_divisao_por_zero(self):
        a = No(
            "a",
            "INPUT",
            valor=10.0
        )

        b = No(
            "b",
            "INPUT",
            valor=0.0
        )

        z = No(
            "z",
            "DIV",
            entradas=[a, b]
        )

        motor = Motor([a, b, z])

        with self.assertRaises(ZeroDivisionError):
            motor.avaliar(z)


# ============================================================
# TESTES DE REPRODUTIBILIDADE DO MONTE CARLO
# ============================================================

class TestesMonteCarlo(unittest.TestCase):

    def executar_monte_carlo(self, diretorio):
        """
        Copia os arquivos necessários para uma pasta temporária
        e executa o Monte Carlo isoladamente.
        """

        arquivos = [
            "motor.py",
            "casos.py",
            "monteCarlos.py",
        ]

        for nome in arquivos:
            origem = DIRETORIO_PROJETO / nome
            destino = diretorio / nome

            if not origem.exists():
                raise FileNotFoundError(
                    f"Arquivo não encontrado: {origem}"
                )

            shutil.copy2(origem, destino)

        processo = subprocess.run(
            [sys.executable, "monteCarlos.py"],
            cwd=str(diretorio),
            capture_output=True,
            text=True,
            timeout=600
        )

        self.assertEqual(
            processo.returncode,
            0,
            msg=(
                "Erro na execução do Monte Carlo.\n"
                f"STDOUT:\n{processo.stdout}\n"
                f"STDERR:\n{processo.stderr}"
            )
        )

        for nome in ARQUIVOS_MONTE_CARLO:
            caminho = diretorio / nome

            self.assertTrue(
                caminho.exists(),
                msg=f"Arquivo não foi gerado: {nome}"
            )

            self.assertGreater(
                caminho.stat().st_size,
                0,
                msg=f"Arquivo vazio: {nome}"
            )

    def test_execucao_produz_resumos_reprodutiveis(self):

        with tempfile.TemporaryDirectory() as temp1:
            with tempfile.TemporaryDirectory() as temp2:

                diretorio1 = Path(temp1)
                diretorio2 = Path(temp2)

                # Primeira execução
                self.executar_monte_carlo(diretorio1)

                # Segunda execução
                self.executar_monte_carlo(diretorio2)

                # Compara os arquivos gerados
                for nome in ARQUIVOS_MONTE_CARLO:

                    arquivo1 = diretorio1 / nome
                    arquivo2 = diretorio2 / nome

                    conteudo1 = arquivo1.read_bytes()
                    conteudo2 = arquivo2.read_bytes()

                    self.assertEqual(
                        conteudo1,
                        conteudo2,
                        msg=(
                            f"O arquivo {nome} apresentou "
                            "resultados diferentes entre execuções."
                        )
                    )


# ============================================================
# EXECUÇÃO DOS TESTES
# ============================================================

if __name__ == "__main__":
    unittest.main(verbosity=2)
