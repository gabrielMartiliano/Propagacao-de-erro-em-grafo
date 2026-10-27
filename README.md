
# Propagação de Erros em Grafos Aritméticos

Projeto acadêmico para analisar a propagação de erros em expressões aritméticas representadas por grafos computacionais (DAGs), comparando os erros reais com estimativas obtidas por análise de sensibilidade e aproximação linear.

## Objetivos

- Avaliar a propagação de perturbações nas entradas de expressões aritméticas.
- Calcular sensibilidades em relação às variáveis de entrada.
- Comparar o erro real com a estimativa linear.
- Utilizar simulações de Monte Carlo para analisar diferentes níveis de perturbação.
- Registrar os resultados dos experimentos em arquivos CSV.

## Estrutura do projeto

```text
Propagacao-de-erro-em-grafo/
├── motor.py
├── casos.py
├── main.py
├── monteCarlos.py
├── resultados_monte_carlo.csv
└── README.md
```

- **motor.py:** implementa o motor de cálculo, a avaliação do grafo e o cálculo de sensibilidades.
- **casos.py:** centraliza os casos de teste, as expressões e os valores esperados.
- **main.py:** executa os testes determinísticos.
- **monteCarlos.py:** executa as simulações de Monte Carlo e salva os resultados em CSV.
- **resultados_monte_carlo.csv:** arquivo gerado com as estatísticas das simulações.

## Requisitos

- Python 3.10 ou superior.
- Não são necessárias bibliotecas externas para a execução básica, pois o projeto utiliza módulos da biblioteca padrão do Python.

## Como executar

Abra o terminal na pasta do projeto.

### 1. Executar os testes determinísticos

```bash
python main.py
```

Essa execução avalia os casos definidos em `casos.py`, calcula as sensibilidades e compara os resultados obtidos com os valores esperados.

### 2. Executar as simulações de Monte Carlo

```bash
python monteCarlos.py
```

O programa executa as simulações para todos os casos cadastrados, utilizando os valores de `delta` configurados no código.

Configuração padrão:

- **Simulações por combinação:** 1.000
- **Valores de delta:** 0.01, 0.1 e 0.5
- **Número de casos:** 4
- **Total previsto:** 12.000 simulações

O total considera quatro casos, três valores de delta e mil simulações para cada combinação.

## Resultados

O programa de Monte Carlo gera o arquivo:

```text
resultados_monte_carlo.csv
```

O arquivo contém estatísticas como:

- Erro real médio, mediano e máximo.
- Percentis 95 (P95) e 99 (P99) do erro real.
- Erro linear médio.
- Diferença média entre o erro real e a estimativa linear.
- Percentual de simulações em que a soma dos módulos das contribuições foi suficiente para cobrir o erro real.

O CSV pode ser aberto em ferramentas como Microsoft Excel, LibreOffice Calc ou pandas para análise posterior.

## Interpretação dos parâmetros

O parâmetro `delta` define o intervalo de perturbação absoluta aplicado às entradas.

Para uma entrada nominal \(x\), a perturbação é sorteada uniformemente no intervalo:

\[
\varepsilon \sim U(-\delta,\delta)
\]

O valor perturbado da entrada é:

\[
x' = x + \varepsilon
\]

Por exemplo, se \(x=2\) e \(\delta=0.1\), o valor perturbado pode variar entre 1.9 e 2.1.

A semente aleatória permite reproduzir a sequência de perturbações nas mesmas condições de execução.

## Casos de teste

O projeto contempla quatro situações:

1. **Perturbação de nó intermediário:** analisa o efeito de uma alteração em um resultado intermediário da expressão.
2. **Ramos convergentes:** avalia a contribuição de uma mesma variável em diferentes caminhos do grafo.
3. **Cancelamento:** verifica o comportamento de contribuições que se anulam.
4. **Divisão válida:** analisa a propagação de erros em uma operação de divisão.

## Observações

- Os resultados dependem das expressões e dos parâmetros definidos nos casos de teste.
- O método de aproximação linear é uma estimativa local e pode diferir do erro real, especialmente em expressões não lineares.
- Os resultados de Monte Carlo representam os cenários amostrados e não constituem, isoladamente, uma garantia matemática para todos os valores possíveis.
- A interpretação da cobertura pela soma dos módulos deve considerar a definição matemática implementada no motor.

