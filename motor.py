"""Motor de propagacao de erros em grafos aritmeticos.

Operacoes suportadas:
    INPUT: no de entrada, com valor numerico
    ADD:   x + y
    SUB:   x - y
    MUL:   x * y
    DIV:   x / y

O motor calcula valores, derivadas locais, sensibilidades globais e
estimativas de primeira ordem para perturbacoes aditivas.
"""

from math import isfinite


class No:
    """Representa uma entrada ou uma operacao do grafo."""

    def __init__(self, nome, operacao, valor=None, entradas=None):
        self.nome = str(nome)
        self.operacao = str(operacao).upper()
        self.valor = valor
        self.entradas = list(entradas) if entradas is not None else []

        # Resultados preenchidos pelo Motor
        self.derivadas = []
        self.sensibilidade = 0.0
        self.valor_calculado = None

    def __repr__(self):
        return f"No(nome={self.nome!r}, operacao={self.operacao!r})"


class Motor:
    """Executa calculos em um grafo aritmetico."""

    OPERACOES_BINARIAS = {"ADD", "SUB", "MUL", "DIV"}

    def __init__(self, nos=None):
        self.nos = list(nos) if nos is not None else []
        self.ordem = []
        self.valores = {}
        self.sensibilidades = {}

    # ------------------------------------------------------------------
    # Organizacao e validacao do grafo
    # ------------------------------------------------------------------

    def _ordenar(self, saida):
        """Retorna os nos em ordem de calculo e detecta ciclos."""
        ordem = []
        estados = {}
        nomes_objetos = {}

        def visitar(no):
            if not isinstance(no, No):
                raise TypeError("Todas as entradas do grafo devem ser objetos No.")

            if no.nome in nomes_objetos and nomes_objetos[no.nome] is not no:
                raise ValueError(
                    f"Existem nos diferentes com o mesmo nome: {no.nome!r}."
                )
            nomes_objetos[no.nome] = no

            estado = estados.get(no.nome, 0)
            if estado == 1:
                raise ValueError(f"O grafo possui um ciclo envolvendo {no.nome!r}.")
            if estado == 2:
                return

            estados[no.nome] = 1

            if no.operacao == "INPUT":
                if no.entradas:
                    raise ValueError(
                        f"O no INPUT {no.nome!r} nao deve possuir entradas."
                    )
            elif no.operacao in self.OPERACOES_BINARIAS:
                if len(no.entradas) != 2:
                    raise ValueError(
                        f"O no {no.nome!r} ({no.operacao}) precisa de duas entradas."
                    )
                for entrada in no.entradas:
                    visitar(entrada)
            else:
                raise ValueError(
                    f"Operacao nao reconhecida no no {no.nome!r}: {no.operacao!r}."
                )

            estados[no.nome] = 2
            ordem.append(no)

        visitar(saida)
        return ordem

    @staticmethod
    def _numero_finito(valor, contexto):
        """Converte um valor para float e rejeita valores nao finitos."""
        try:
            numero = float(valor)
        except (TypeError, ValueError) as erro:
            raise ValueError(f"Valor numerico invalido em {contexto}: {valor!r}.") from erro

        if not isfinite(numero):
            raise ValueError(f"O valor em {contexto} precisa ser finito.")
        return numero

    # ------------------------------------------------------------------
    # Calculo de cada operacao e suas derivadas locais
    # ------------------------------------------------------------------

    def _calcular_no(self, no, valores):
        """Retorna (valor do no, derivadas locais em relacao as entradas)."""
        if no.operacao == "INPUT":
            if no.valor is None:
                raise ValueError(f"A entrada {no.nome!r} nao possui valor.")
            return self._numero_finito(no.valor, f"entrada {no.nome!r}"), []

        x = valores[no.entradas[0].nome]
        y = valores[no.entradas[1].nome]

        if no.operacao == "ADD":
            valor = x + y
            derivadas = [1.0, 1.0]
        elif no.operacao == "SUB":
            valor = x - y
            derivadas = [1.0, -1.0]
        elif no.operacao == "MUL":
            valor = x * y
            derivadas = [y, x]
        elif no.operacao == "DIV":
            if y == 0.0:
                raise ZeroDivisionError(f"Divisao por zero no no {no.nome!r}.")
            valor = x / y
            derivadas = [1.0 / y, -x / (y * y)]
        else:  # Protecao adicional; a operacao ja e validada em _ordenar.
            raise ValueError(f"Operacao nao reconhecida: {no.operacao!r}.")

        valor = self._numero_finito(valor, f"resultado do no {no.nome!r}")
        derivadas = [
            self._numero_finito(d, f"derivada local do no {no.nome!r}")
            for d in derivadas
        ]
        return valor, derivadas

    # ------------------------------------------------------------------
    # Avaliacao do grafo
    # ------------------------------------------------------------------

    def avaliar_todos(self, saida, perturbacoes=None):
        """Calcula e retorna os valores de todos os nos usados pela saida.

        perturbacoes e um dicionario {nome_do_no: delta}. O delta e somado
        ao valor calculado daquele no, antes de alimentar os nos seguintes.
        Assim, e possivel perturbar entradas ou nos intermediarios.
        """
        perturbacoes = perturbacoes or {}
        if not isinstance(perturbacoes, dict):
            raise TypeError("perturbacoes deve ser um dicionario {nome: delta}.")

        self.ordem = self._ordenar(saida)
        valores = {}

        nomes_validos = {no.nome for no in self.ordem}
        nomes_desconhecidos = set(perturbacoes) - nomes_validos
        if nomes_desconhecidos:
            raise ValueError(
                "Perturbacoes informadas para nos fora do grafo: "
                + ", ".join(sorted(map(str, nomes_desconhecidos)))
            )

        deltas = {
            nome: self._numero_finito(delta, f"perturbacao de {nome!r}")
            for nome, delta in perturbacoes.items()
        }

        for no in self.ordem:
            valor, derivadas = self._calcular_no(no, valores)
            valor += deltas.get(no.nome, 0.0)
            valor = self._numero_finito(valor, f"valor perturbado do no {no.nome!r}")

            no.derivadas = derivadas
            no.valor_calculado = valor
            valores[no.nome] = valor

        self.valores = valores
        return dict(valores)

    def avaliar(self, saida, perturbacoes=None):
        """Calcula o valor final do grafo; mantem uma interface simples."""
        return self.avaliar_todos(saida, perturbacoes)[saida.nome]

    # ------------------------------------------------------------------
    # Sensibilidade global: derivada da saida em relacao a cada no
    # ------------------------------------------------------------------

    def calcular_sensibilidades(self, saida):
        """Calcula d(saida)/d(no) por retropropagacao das derivadas.

        As sensibilidades sao calculadas no ponto nominal, sem perturbacoes.
        """
        self.avaliar_todos(saida)
        sensibilidades = {no.nome: 0.0 for no in self.ordem}
        sensibilidades[saida.nome] = 1.0

        for no in reversed(self.ordem):
            for entrada, derivada in zip(no.entradas, no.derivadas):
                sensibilidades[entrada.nome] += (
                    sensibilidades[no.nome] * derivada
                )

        for no in self.ordem:
            no.sensibilidade = sensibilidades[no.nome]

        self.sensibilidades = dict(sensibilidades)
        return dict(sensibilidades)

    def calcular_derivadas_locais(self, saida):
        """Calcula valores e devolve as derivadas locais de cada operacao."""
        self.avaliar_todos(saida)
        return {
            no.nome: list(no.derivadas)
            for no in self.ordem
        }

    # ------------------------------------------------------------------
    # Estimativas de primeira ordem para propagacao de perturbacoes
    # ------------------------------------------------------------------

    def estimar_variacao_linear(self, saida, perturbacoes):
        """Estima delta_saida ~= soma((d saida/d no) * delta_no).

        A aproximacao considera as perturbacoes informadas independentes
        como variaveis de entrada do calculo linear. E uma aproximacao local,
        nao uma garantia de limite para o erro real.
        """
        sensibilidades = self.calcular_sensibilidades(saida)
        nomes_validos = set(sensibilidades)
        desconhecidos = set(perturbacoes) - nomes_validos
        if desconhecidos:
            raise ValueError(
                "Perturbacoes informadas para nos fora do grafo: "
                + ", ".join(sorted(map(str, desconhecidos)))
            )

        variacao = 0.0
        for nome, delta in perturbacoes.items():
            delta = self._numero_finito(delta, f"perturbacao de {nome!r}")
            variacao += sensibilidades[nome] * delta

        return self._numero_finito(variacao, "variacao linear estimada")

    def calcular_contribuicoes(self, saida, perturbacoes):
        """Retorna a contribuicao assinada de cada no: sensibilidade * delta."""
        sensibilidades = self.calcular_sensibilidades(saida)
        contribuicoes = {}

        for nome, delta in perturbacoes.items():
            if nome not in sensibilidades:
                raise ValueError(f"No {nome!r} nao encontrado no grafo.")
            delta = self._numero_finito(delta, f"perturbacao de {nome!r}")
            contribuicoes[nome] = sensibilidades[nome] * delta

        return contribuicoes

    def estimar_magnitude_linear(self, saida, perturbacoes):
        """Soma os modulos das contribuicoes lineares individuais.

        Esta soma e uma estimativa conservadora dentro do modelo linear,
        mas nao e necessariamente um limite para o erro real nao linear.
        """
        contribuicoes = self.calcular_contribuicoes(saida, perturbacoes)
        return sum(abs(valor) for valor in contribuicoes.values())

    def analisar_perturbacoes(self, saida, perturbacoes):
        """Compara a saida nominal, a perturbada e a aproximacao linear."""
        nominal = self.avaliar(saida)
        sensibilidades = self.calcular_sensibilidades(saida)
        contribuicoes = self.calcular_contribuicoes(saida, perturbacoes)
        variacao_linear = sum(contribuicoes.values())

        valor_perturbado = self.avaliar(saida, perturbacoes)
        variacao_real = valor_perturbado - nominal

        return {
            "saida_nominal": nominal,
            "saida_perturbada": valor_perturbado,
            "variacao_real": variacao_real,
            "erro_absoluto_real": abs(variacao_real),
            "variacao_linear_estimada": variacao_linear,
            "erro_absoluto_linear": abs(variacao_linear),
            "diferenca_real_linear": variacao_real - variacao_linear,
            "modulo_diferenca_real_linear": abs(variacao_real - variacao_linear),
            "sensibilidades": sensibilidades,
            "contribuicoes_assinadas": contribuicoes,
            "soma_modulos_contribuicoes": sum(
                abs(valor) for valor in contribuicoes.values()
            ),
        }
