# Simulador para Análise da Propagação de Erros em Grafos de Fluxo de Dados

## Apresentação

Neste Trabalho de Conclusão de Curso em Ciência da Computação, desenvolvi e avaliei um simulador para analisar como perturbações em valores de entrada e em nós intermediários se propagam por grafos aritméticos direcionados acíclicos (DAGs).

Implementei o simulador em Python. O motor avalia os nós do grafo, calcula derivadas locais, propaga as sensibilidades da saída em sentido reverso e compara a variação real provocada por uma perturbação com a estimativa obtida pela aproximação linear de primeira ordem.

## Funcionalidades implementadas

- Representação de grafos aritméticos por nós e dependências.
- Operações `INPUT`, `ADD`, `SUB`, `MUL` e `DIV`.
- Ordenação dos nós para avaliação e detecção de ciclos.
- Cálculo dos valores nominais e das derivadas locais.
- Cálculo reverso das sensibilidades globais, incluindo a acumulação de contribuições em caminhos convergentes.
- Aplicação de perturbações e cálculo da variação real, da estimativa linear e do resíduo.
- Validação por casos determinísticos, testes automatizados e experimentos de Monte Carlo.

## Organização dos arquivos

```text
TCC/
├── figuras/                         # Gráficos utilizados na monografia
├── resultados/                      # CSVs dos experimentos analisados
├── benchmark_complexidade.csv       # Tempos medidos no benchmark
├── benchmark_complexidade.py        # Mede o tempo de análise do motor
├── casos.py                         # Define os quatro casos determinísticos
├── experimento_abrangente.py        # Experimento com ADD, SUB, MUL e DIV
├── experimento_precisao.py          # Experimento escalável de precisão
├── gerar_figuras.py                 # Gera as figuras a partir dos CSVs
├── main.py                          # Executa os casos determinísticos
├── main.tex                         # Fonte LaTeX da monografia
├── monteCarlos.py                   # Executa o Monte Carlo dos casos
├── motor.py                         # Implementação do motor de propagação
├── Monografia_TCC_Revisada.pdf      # Monografia compilada
├── REFERENCIAS_COMPLEMENTARES.md    # Links e DOIs de leituras complementares
├── testes_validacao.py              # Testes principais
└── testes_validacao_avancada.py     # Testes adicionais
```

## Componentes do projeto

### Motor e casos determinísticos

Em `motor.py`, implementei as classes `No` e `Motor`, responsáveis pela representação e avaliação dos grafos. Em `casos.py`, organizei quatro casos de referência com valores esperados calculados analiticamente. O arquivo `main.py` executa esses casos e compara os resultados obtidos com os valores esperados.

### Testes automatizados

Os arquivos `testes_validacao.py` e `testes_validacao_avancada.py` reúnem 21 métodos de teste. Eles verificam, entre outros pontos, os valores calculados, as sensibilidades, as derivadas, a detecção de ciclos, as condições inválidas e a consistência do motor.

### Experimento de Monte Carlo

`monteCarlos.py` avalia os quatro casos de referência com perturbações aditivas. São utilizadas três intensidades (`0,01`, `0,1` e `0,5`), 1.000 simulações por caso e intensidade e semente pseudoaleatória `20261027`, totalizando 12.000 amostras. Os resultados individuais e os resumos são gravados em CSV.

### Experimento escalável de precisão

`experimento_precisao.py` avalia grafos cuja saída é formada pela soma de produtos entre pares de entradas. São considerados 4, 8, 16 e 32 valores de entrada, quatro intensidades de perturbação absoluta (`0,001`, `0,01`, `0,05` e `0,10`) e 1.000 simulações por configuração. O experimento totaliza 16 configurações e 16.000 amostras, com semente `20261107`.

### Experimento abrangente

`experimento_abrangente.py` avalia as operações `ADD`, `SUB`, `MUL` e `DIV`, em estruturas de cadeia e ramificadas, com quatro tamanhos, quatro intensidades relativas e três padrões de sinal das perturbações. O delineamento contém 384 configurações, com 1.000 simulações por configuração, totalizando 384.000 amostras.

### Benchmark de tempo

`benchmark_complexidade.py` mede o tempo de execução da análise completa do motor em cadeias de adição com sete tamanhos. Para cada tamanho, são realizadas cinco chamadas de aquecimento e 30 medições. O CSV `benchmark_complexidade.csv` contém os tempos e estatísticas usados na análise log-log da monografia.

O benchmark foi medido em Windows 10, com Python 3.14, processador AMD Ryzen 5 5600G, 16 GB de memória DDR4-3200 MHz e placa de vídeo AMD Radeon RX 6600. A medição executa operações escalares em CPU; a GPU não é utilizada.

## Instalação das dependências

O motor, os casos determinísticos, os testes e o benchmark utilizam a biblioteca padrão do Python. Para executar os experimentos e gerar os gráficos, instale:

```powershell
python -m pip install matplotlib numpy pandas
```

Utilize Python 3.14 para reproduzir o ambiente de referência do benchmark. Outras versões podem funcionar, mas podem produzir tempos diferentes.

## Como executar

Execute os comandos a partir da pasta principal do projeto.

### 1. Executar os casos determinísticos

```powershell
python main.py
```

### 2. Executar os testes automatizados

```powershell
python -m unittest -v testes_validacao testes_validacao_avancada
```

### 3. Executar os experimentos

```powershell
python monteCarlos.py
python experimento_precisao.py
python experimento_abrangente.py
python benchmark_complexidade.py
```

### 4. Gerar as figuras

```powershell
python gerar_figuras.py
```

O gerador utiliza os CSVs disponíveis na pasta principal ou em `resultados/` e grava as figuras finais em `figuras/`. A execução dos scripts experimentais pode criar novos CSVs e imagens na pasta principal, substituindo arquivos de mesmo nome. Para preservar os resultados que acompanham a monografia, mantenha uma cópia dos arquivos existentes em `resultados/` antes de executar novamente os experimentos.

## Compilação da monografia

O arquivo `main.tex` contém a fonte da monografia e o bloco bibliográfico necessário para gerar `referencias.bib`. Com uma distribuição LaTeX instalada, compile a partir da pasta principal:

```powershell
pdflatex main.tex
bibtex main
pdflatex main.tex
pdflatex main.tex
```

O arquivo `Monografia_TCC_Revisada.pdf` é a versão compilada que acompanha o projeto. O documento `REFERENCIAS_COMPLEMENTARES.md` reúne links e DOIs de materiais complementares; as referências citadas na monografia estão registradas no bloco bibliográfico do `main.tex`.

## Convenção do resíduo

Em todos os experimentos, o resíduo assinado é definido por:

\[
R = \Delta o_{\mathrm{real}} - \Delta o_{\mathrm{lin}}.
\]

O viés corresponde à média dos resíduos assinados. As métricas baseadas em módulo ou quadrado do resíduo, como MAE e RMSE, são calculadas a partir dessa mesma definição.

## Observação sobre os resultados

Os arquivos CSV de `resultados/` e as figuras de `figuras/` são os materiais utilizados na elaboração das tabelas e figuras da monografia. A reexecução dos experimentos pode gerar novas amostras, pois os resultados dependem das sementes pseudoaleatórias, das versões das bibliotecas e do ambiente de execução. Para reproduzir os valores apresentados no PDF, utilize os CSVs já incluídos no projeto; para realizar novas execuções, utilize os scripts Python correspondentes.
