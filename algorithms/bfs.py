"""Busca em Largura (BFS) para o problema dos 4 cavalos (tabuleiro 3x3).

Implementação fiel ao pseudocódigo do Algoritmo Básico de Busca, com
abertos como Fila (primeiro a entrar, primeiro a sair → BFS):

    Algoritmo Básico de Busca
    Início
        Defina(abertos); S := raiz; Fracasso := F; Sucesso := F;
        Insere(S, abertos); Defina(fechados);
        Enquanto não (Sucesso ou Fracasso) faça
            Se abertos = vazio então Fracasso := T;
            Senão
                N := Primeiro(abertos); {Pilha(topo), Fila(primeiro)}
                Se N = solução então Sucesso := T;
                Senão
                    Enquanto R(N) <> vazio faça
                        Escolha r de R(N); New(u);
                        u := r(N); Insere(u, abertos);
                        Atualiza R(N);
                    Fim-enquanto;
                    Insere(N, fechados); {Destrua(N)}
                Fim-se;
            Fim-se;
        Fim-enquanto;
    Fim.

Sucessores cujo estado já está em abertos ou fechados são descartados
(evita reexpandir estados repetidos). Como a fila expande os nós por
níveis, o BFS garante a solução com o menor número de movimentos.

A escolha de r em R(N) segue a ordem definida pelo parâmetro `order`:
  "asc"  → r1, r2, ..., r16  (padrão)
  "desc" → r16, r15, ..., r1
"""

from collections import deque

from utils import RULES, INITIAL_STATE, is_goal, apply_rule, show_board


def state_key(state):
    """Representação hasheável do estado, para abertos/fechados/parent."""
    return tuple(state[sq] for sq in range(1, 10))


def applicable_rules(state, order="asc"):
    """Regras em R(N): precondição ok (origem ocupada, destino vazio)."""
    names = [
        rule
        for rule, (origin, dest) in RULES.items()
        if state[origin] is not None and state[dest] is None
    ]
    return list(reversed(names)) if order == "desc" else names


def rebuild_path(state, parent):
    """Reconstrói (caminho, regras aplicadas) de S até `state` via parent."""
    path, applied = [state], []
    while parent[state_key(state)] is not None:
        state, rule = parent[state_key(state)]
        path.append(state)
        applied.append(rule)
    return path[::-1], applied[::-1]


def print_solution(path, applied, order="asc"):
    """Caminho que deu certo: em cada passo, as possibilidades e a regra aplicada."""
    print()
    print("Estado inicial:")
    show_board(path[0])
    for i, rule in enumerate(applied):
        possibilities = applicable_rules(path[i], order=order)
        origin, dest = RULES[rule]
        print(f"\nPasso {i + 1}: {rule} ({origin} -> {dest})")
        print(f"  possibilidades: {', '.join(possibilities) if possibilities else '(nenhuma)'}")
        print(f"  aplica {rule}")
        show_board(path[i + 1])


def bfs(initial_state, order="asc"):
    """Retorna (caminho, regras aplicadas, stats, parent) se achar solução, ou None.

    stats  = {"expanded": nós expandidos, "max_open": tamanho máximo de abertos}
    parent = dict estado_key → (estado_pai, regra) | None (para reconstruir/plotar a árvore)
    """
    opened = deque([initial_state])           # abertos (Fila)
    seen = {state_key(initial_state)}         # estados em abertos ou fechados
    parent = {state_key(initial_state): None} # para reconstruir o caminho S-N
    stats = {"expanded": 0, "max_open": 1}
    success = failure = False
    result = None

    while not (success or failure):
        if not opened:  # abertos = vazio
            failure = True
        else:
            N = opened.popleft()  # N := Primeiro(abertos) {Fila}
            if is_goal(N):  # N = solução
                success = True
                result = rebuild_path(N, parent)
            else:
                stats["expanded"] += 1
                for rule in applicable_rules(N, order=order):  # Enquanto R(N) <> vazio
                    u = apply_rule(rule, N)  # u := r(N)
                    if state_key(u) in seen:  # já em abertos ou fechados
                        continue
                    seen.add(state_key(u))
                    parent[state_key(u)] = (N, rule)
                    opened.append(u)  # Insere(u, abertos)
                stats["max_open"] = max(stats["max_open"], len(opened))
                # Insere(N, fechados) — já registrado em `seen`

    if not success:
        return None
    path, applied = result
    return path, applied, stats, parent


def plot_tree(path, parent, order="asc", figsize=(22, 14)):
    """Plota a árvore de busca BFS com matplotlib + networkx.

    Cada nó é um círculo; nós do caminho solução são destacados em laranja.
    O layout é hierárquico (eixo Y = profundidade, nós do mesmo nível
    distribuídos horizontalmente). Arestas são rotuladas com a regra aplicada.
    """
    import matplotlib.pyplot as plt
    import networkx as nx

    G = nx.DiGraph()
    depth = {}  # state_key → profundidade
    label_map = {}  # state_key → rótulo exibido no nó

    # Reconstituir estados a partir do parent (chave → estado reconstruído)
    # Precisamos do estado completo para montar as labels; guardamos nos valores
    # já que parent[k] = (estado_pai, regra) ou None.
    # Construímos a lista de todos os estados a partir do parent dict.
    key_to_state = {}

    # O estado raiz não tem entrada com pai; reconstruímos percorrendo as arestas
    # de forma inversa a partir do parent dict (que já tem tudo).
    for k, v in parent.items():
        if v is None:
            depth[k] = 0
        # estados filhos têm profundidade calculada abaixo

    # BFS pela árvore de parent para calcular profundidades e adicionar arestas
    queue = deque([k for k, v in parent.items() if v is None])
    while queue:
        k = queue.popleft()
        for child_k, val in parent.items():
            if val is not None and state_key(val[0]) == k and child_k not in depth:
                depth[child_k] = depth[k] + 1
                G.add_edge(k, child_k, rule=val[1])
                queue.append(child_k)

    # Fallback: calcular profundidade para nós que sobraram
    for k in parent:
        if k not in depth:
            depth[k] = -1

    # Nós do caminho solução
    solution_keys = {state_key(s) for s in path}

    # Layout hierárquico: agrupar por nível
    levels = {}
    for k, d in depth.items():
        levels.setdefault(d, []).append(k)

    pos = {}
    for d, nodes in levels.items():
        for i, k in enumerate(nodes):
            pos[k] = (i - len(nodes) / 2, -d)

    # Cores dos nós
    node_colors = [
        "#F4A261" if k in solution_keys else "#AED6F1"
        for k in G.nodes()
    ]
    node_sizes = [
        500 if k in solution_keys else 200
        for k in G.nodes()
    ]

    fig, ax = plt.subplots(figsize=figsize)
    nx.draw_networkx_nodes(G, pos, node_color=node_colors, node_size=node_sizes, ax=ax)
    nx.draw_networkx_edges(G, pos, arrows=True, arrowsize=10,
                           edge_color="#888888", ax=ax)

    # Labels nas arestas (só para o caminho solução, evita poluição)
    solution_path_keys = set(zip(
        [state_key(s) for s in path[:-1]],
        [state_key(s) for s in path[1:]],
    ))
    edge_labels = {
        (u, v): d["rule"]
        for u, v, d in G.edges(data=True)
        if (u, v) in solution_path_keys
    }
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels,
                                 font_size=7, ax=ax)

    # Legenda manual
    from matplotlib.patches import Patch
    legend = [
        Patch(facecolor="#F4A261", label="Caminho solução"),
        Patch(facecolor="#AED6F1", label="Outros nós explorados"),
    ]
    ax.legend(handles=legend, loc="upper right")
    ax.set_title(
        f"Árvore BFS — {len(G.nodes())} nós, profundidade máx. {max(depth.values())}, "
        f"solução em profundidade {len(path) - 1}",
        fontsize=12,
    )
    ax.axis("off")
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    result = bfs(INITIAL_STATE)
    if result is None:
        print("Fracasso: abertos esvaziou sem encontrar solução.")
    else:
        path, applied, stats, parent = result
        print(f"Sucesso! Solução ótima com {len(applied)} movimentos "
              f"({stats['expanded']} nós expandidos, máx. de abertos = {stats['max_open']}):")
        print(" -> ".join(applied))
        print_solution(path, applied)
