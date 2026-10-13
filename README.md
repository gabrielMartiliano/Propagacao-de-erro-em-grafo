# 🕸️ Analisador Estático de Propagação de Erro em DFG

> **Ferramenta  Interativa para Simulação Analítica de Propagação de Erro em Computação Aproximada**

Este repositório contém o código-fonte do simulador desenvolvido como Trabalho de Conclusão de Curso (TCC) em Ciência da Computação na Universidade Federal do Tocantins (UFT). 

O projeto propõe um ecossistema web ágil para a validação visual de modelos matemáticos analíticos em circuitos aproximados, substituindo a necessidade de execuções demoradas de simulações estatísticas (como o Método de Monte Carlo) durante a Exploração do Espaço de Conceção (DSE).

---

## ✨ Funcionalidades


---

## 📚 Fundamentação Teórica

O algoritmo de análise estática deste simulador foi destilado a partir de três referências centrais na literatura de Computação Aproximada:

1. **Filtro de Criticidade e Operações Resilientes:** Isolamento arquitetural de operações multiplicativas vs. aditivas (*Estimate and Recompute - Gao & Qu, 2018*).
2. **Isolamento de Impacto de Falhas:** Métrica MRED calculada assumindo o restante do circuito operando em modo exato (*ACHILLES - Tabatabaei-Nikkhah et al., 2018*).
3. **Amplificação de Erro via Derivadas Parciais:** Propagação determinística top-down usando os limites máximos admissíveis de entrada (*TDApprox - Ansaloni et al., 2020*).

---

## 🛠️ Stack Tecnológica



---

## 🚀 Como Executar o Projeto


1. **Clone o repositório:**
   ```bash
   git clone [https://github.com/gabrielMartiliano/Propaga-o-de-erro-em-grafo-de-opera-es.git](https://github.com/gabrielMartiliano/Propaga-o-de-erro-em-grafo-de-opera-es.git)
