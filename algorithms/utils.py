"""
Estruturas comuns a todos os algoritmos de busca:

- RULES: regras de transição, em ordem crescente (r1, r2, ...)
- INITIAL_STATE: estado inicial do tabuleiro
- is_goal: teste de objetivo
- apply_rule: aplica uma regra a um estado, gerando o novo estado
- show_board: imprime o tabuleiro
- COST_FUNCTIONS / path_cost: funções de custo real das regras
"""

# Regras de transição: cada regra é um movimento de cavalo (origem, destino),
RULES = {
    "r1": (1, 6),
    "r2": (1, 8),
    "r3": (2, 7),
    "r4": (2, 9),
    "r5": (3, 4),
    "r6": (3, 8),
    "r7": (4, 3),
    "r8": (4, 9),
    "r9": (6, 1),
    "r10": (6, 7),
    "r11": (7, 2),
    "r12": (7, 6),
    "r13": (8, 1),
    "r14": (8, 3),
    "r15": (9, 2),
    "r16": (9, 4),
}

# Estado inicial do tabuleiro
INITIAL_STATE = {
    1: "bx", 2: None, 3: "by",
    4: None, 5: None, 6: None,
    7: "px", 8: None, 9: "py",
}

# Teste de objetivo: Pretas nas casas 1 e 3, brancas nas casas 7 e 9 (qualquer combinação).
def is_goal(state):
    top_black = all(state[sq] is not None and state[sq][0] == "p" for sq in (1, 3))
    bottom_white = all(state[sq] is not None and state[sq][0] == "b" for sq in (7, 9))
    return top_black and bottom_white # Retorna True se o estado for objetivo, False caso contrário

# Aplicação de regra: Retorna o novo estado após mover o cavalo de origem para destino.
def apply_rule(rule, state):
    origin, dest = RULES[rule]
    new_state = dict(state)
    new_state[dest] = new_state[origin]
    new_state[origin] = None
    return new_state

# Print do tabuleiro
def show_board(state):
    for row in ((1, 2, 3), (4, 5, 6), (7, 8, 9)):
        print(" ".join(state[sq] or "--" for sq in row))


# ── Funções de custo real (Busca Ordenada) ────────────────────────────────────
# Cada função recebe (rule, state) e devolve o custo (inteiro > 0) de aplicar a
# regra ao estado. `state` é o estado ANTES do movimento.

def _row(sq):
    """Linha (0, 1 ou 2) da casa sq."""
    return (sq - 1) // 3

# Custo pela direção do movimento: brancas querem chegar à linha de baixo
# (casas 7-8-9) e pretas à linha de cima (casas 1-2-3).
#   aproxima da linha-objetivo → 1
#   afasta da linha-objetivo   → 3
# Num tabuleiro 3x3 todo salto de cavalo muda de linha, logo não existe
# movimento "lateral" (mesma distância); a função só devolve 1 ou 3.
def cost_direction(rule, state):
    origin, dest = RULES[rule]
    piece = state[origin]
    goal_row = 2 if piece[0] == "b" else 0
    before = abs(_row(origin) - goal_row)
    after = abs(_row(dest) - goal_row)
    return 1 if after < before else 3

# Custo pela casa de destino, independente da peça:
#   canto (1, 3, 7, 9) → 1
#   borda (2, 4, 6, 8) → 2
# (a casa central 5 nunca é alcançada por um cavalo no 3x3)
def cost_destination(rule, state):
    _, dest = RULES[rule]
    return 1 if dest in (1, 3, 7, 9) else 2

COST_FUNCTIONS = {
    "direcao": cost_direction,
    "destino": cost_destination,
}

# Custo total de uma sequência de regras aplicada a partir de initial_state.
def path_cost(applied, initial_state, cost):
    cost_fn = COST_FUNCTIONS[cost] if isinstance(cost, str) else cost
    state, total = initial_state, 0
    for rule in applied:
        total += cost_fn(rule, state)
        state = apply_rule(rule, state)
    return total
