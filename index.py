import json

class GrafoNode:
    def __init__(self, node_id, op_type, value=None):
        self.node_id = node_id
        self.op_type = op_type      # 'INPUT', 'ADD', 'MUL'
        self.value = value          # Valor nominal
        self.inputs = []            # Nós de entrada
        self.is_sensitive = False   # Classificação estática (Sensível/Resiliente)
        self.k_coeffs = []          # Coeficientes de propagação (k)
        self.peso_saida = 0.0       # Impacto total na saída (Multiplicador de erro)

    def conectar_entrada(self, node):
        self.inputs.append(node)
        self.k_coeffs.append(1.0)

class AnalisadorEstatico:
    def __init__(self, nos):
        self.nos = nos

    def classificar_criticidade(self):
        """
        Aplica a regra de classificação imediata. 
        Operações como Multiplicação são marcadas como 'Sensíveis a Erro'.
        """
        for node in self.nos:
            if node.op_type in ['MUL', 'DIV']:
                node.is_sensitive = True
            else:
                node.is_sensitive = False

    def calcular_valores_nominais_e_coeficientes(self, saida_node):
        """
           Derivadas Parciais
        """
        if saida_node.op_type == 'INPUT':
            return saida_node.value

        for node in saida_node.inputs:
            if node.value is None:
                self.calcular_valores_nominais_e_coeficientes(node)

        if saida_node.op_type == 'ADD':
            saida_node.value = saida_node.inputs[0].value + saida_node.inputs[1].value
            # Na adição, o erro passa reto (k1=1, k2=1)
            saida_node.k_coeffs[0] = 1.0
            saida_node.k_coeffs[1] = 1.0
            
        elif saida_node.op_type == 'MUL':
            saida_node.value = saida_node.inputs[0].value * saida_node.inputs[1].value
            # Na multiplicação, o erro é amplificado pela entrada oposta
            saida_node.k_coeffs[0] = abs(saida_node.inputs[1].value)
            saida_node.k_coeffs[1] = abs(saida_node.inputs[0].value)
            
        return saida_node.value

    def propagar_impacto_reverso(self, saida_node):
        """
        Acumula os coeficientes para descobrir o peso exato que um erro 
        local terá lá no final do circuito.
        """
        saida_node.peso_saida = 1.0
        fila = [saida_node]
        
        while fila:
            atual = fila.pop(0)
            for i, entrada_node in enumerate(atual.inputs):
                # O peso é o impacto do nó atual * a amplificação (k) desta aresta
                peso_acumulado = atual.peso_saida * atual.k_coeffs[i]
                entrada_node.peso_saida += peso_acumulado
                
                if entrada_node not in fila:
                    fila.append(entrada_node)

    def simular_injecao_isolada(self, delta_erro):
        """
        Simula a injeção de erro OAT (One-At-a-Time).
        """
        resultados = []
        for node in self.nos:
            impacto_final = delta_erro * node.peso_saida
            resultados.append({
                "id": node.node_id,
                "tipo": node.op_type,
                "sensivel": node.is_sensitive,
                "peso_propagacao": node.peso_saida,
                "erro_projetado_na_saida": impacto_final
            })
        return resultados

# ==========================================
# TESTE DO MOTOR (Simulando Y = (A + B) * C)
# ==========================================

# 1. Instanciando o Grafo
node_a = GrafoNode("Input_A", "INPUT", value=2.0)
node_b = GrafoNode("Input_B", "INPUT", value=3.0)
node_c = GrafoNode("Input_C", "INPUT", value=10.0)

node_add = GrafoNode("Somador_1", "ADD")
node_add.conectar_entrada(node_a)
node_add.conectar_entrada(node_b)

node_mul = GrafoNode("Multiplicador_1", "MUL")
node_mul.conectar_entrada(node_add)
node_mul.conectar_entrada(node_c)

todos_os_nos = [node_a, node_b, node_c, node_add, node_mul]

# 2. Rodando o Analisador
analisador = AnalisadorEstatico(todos_os_nos)
analisador.classificar_criticidade()
analisador.calcular_valores_nominais_e_coeficientes(node_mul)
analisador.propagar_impacto_reverso(node_mul)

# 3. Gerando o laudo estático para a interface visual
delta_teste = 0.5 # Injetando um pequeno erro de 0.5
laudo = analisador.simular_injecao_isolada(delta_teste)

print(json.dumps(laudo, indent=2))