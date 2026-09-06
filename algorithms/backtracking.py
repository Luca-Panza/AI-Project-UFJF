"""Algoritmo de Backtracking para o problema dos 4 cavalos (tabuleiro 3x3).

Implementação fiel ao pseudocódigo:

    Algoritmo Backtracking
    Início
        S := estado inicial;
        N := S;
        Fracasso := F;
        Sucesso := F;
        Enquanto não (Sucesso ou Fracasso) faça
            Se nível (N) >= p então (p -> limite de profundidade da busca)
                N := pai(N);
            Fim-se;
            Selecione o operador r de R(N); (*)
            Se R(N) <> vazio então
                N := r(N);
                Se N é solução então
                    Sucesso := T;
                Fim-se;
            Senão
                Se N = S então
                    Fracasso := T;
                Senão
                    N := pai(N);
                Fim-se;
            Fim-se;
        Fim-enquanto;
    Fim.

    (*) r é aplicável a N se r(N) não está no caminho S-N (evita ciclos).

A seleção do operador segue a ordem definida pelo parâmetro `order`:
  "asc"  → r1, r2, ..., r16  (padrão)
  "desc" → r16, r15, ..., r1
"""

from utils import RULES, INITIAL_STATE, is_goal, apply_rule, show_board

# Limite de profundidade da busca (p). A solução ótima tem 16 movimentos, mas o
# backtracking puro com ordem fixa de regras leva horas para achá-la com p = 16;
# limites maiores encontram soluções (mais longas) em menos de um segundo.
P = 36


def remaining_rules(state, path, tried=None):
    """Regras em R(N): precondição ok, não tentadas neste nó, r(N) fora de S-N."""
    tried = tried or set()
    names = []
    for rule in RULES:
        if rule in tried:
            continue
        origin, dest = RULES[rule]
        if state[origin] is None or state[dest] is not None:
            continue
        if apply_rule(rule, state) in path:
            continue
        names.append(rule)
    return names


def select_rule(state, path, tried, order="asc"):
    """Seleciona o operador r de R(N).

    order="asc"  → regra de menor índice (r1 primeiro)
    order="desc" → regra de maior índice (r16 primeiro)

    Retorna (regra, novo_estado) ou (None, None) se R(N) é vazio.
    """
    remaining = remaining_rules(state, path, tried)
    if not remaining:
        return None, None
    rule = remaining[-1] if order == "desc" else remaining[0]
    return rule, apply_rule(rule, state)


def print_solution(path, applied, tried):
    """Caminho que deu certo: em cada passo, as possibilidades, os recuos daquele nó e a regra aplicada."""
    print()
    print("Estado inicial:")
    show_board(path[0])
    for i, rule in enumerate(applied):
        possibilities = remaining_rules(path[i], path[: i + 1])
        recuos = [r for r in RULES if r in tried[i] and r != rule]
        origin, dest = RULES[rule]
        print(f"\nPasso {i + 1}: {rule} ({origin} -> {dest})")
        print(f"  possibilidades: {', '.join(possibilities) if possibilities else '(nenhuma)'}")
        print(f"  recuos neste nó: {', '.join(recuos) if recuos else '(nenhuma)'}")
        print(f"  aplica {rule}")
        show_board(path[i + 1])


def backtracking(initial_state, depth_limit=None, order="asc"):
    """Retorna (caminho, regras aplicadas, tentadas) se achar solução, ou None.

    order="asc"  → tenta r1 antes de r16  (padrão)
    order="desc" → tenta r16 antes de r1
    """
    if depth_limit is None:
        depth_limit = P
    path = [initial_state]  # caminho S-N; N = path[-1], pai(N) = path[-2]
    tried = [set()]         # regras já tentadas em cada nó do caminho
    applied = []            # regras aplicadas ao longo do caminho
    success = failure = False

    while not (success or failure):
        # Se nível(N) >= p então N := pai(N)
        if len(path) - 1 >= depth_limit:
            path.pop()
            tried.pop()
            applied.pop()

        N = path[-1]
        rule, new_state = select_rule(N, path, tried[-1], order=order)
        if rule is not None:  # R(N) <> vazio
            tried[-1].add(rule)
            path.append(new_state)  # N := r(N)
            tried.append(set())
            applied.append(rule)
            if is_goal(new_state):
                success = True
        else:
            if len(path) == 1:  # N = S
                failure = True
            else:  # N := pai(N)
                path.pop()
                tried.pop()
                applied.pop()

    return (path, applied, tried) if success else None


if __name__ == "__main__":
    result = backtracking(INITIAL_STATE)
    if result is None:
        print(f"Fracasso: nenhuma solução encontrada com limite de profundidade p = {P}.")
    else:
        path, applied, tried = result
        print(f"Sucesso! Solução com {len(applied)} movimentos (p = {P}):")
        print(" -> ".join(applied))
        print_solution(path, applied, tried)
