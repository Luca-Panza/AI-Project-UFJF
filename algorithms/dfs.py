"""Busca em Profundidade (DFS) para o problema dos 4 cavalos (tabuleiro 3x3).

Implementação fiel ao pseudocódigo do Algoritmo Básico de Busca, com
abertos como Pilha (primeiro a entrar, último a sair → DFS):

    Algoritmo Básico de Busca
    Início
        Defina(abertos); S := raiz; Fracasso := F; Sucesso := F;
        Insere(S, abertos); Defina(fechados);
        Enquanto não (Sucesso ou Fracasso) faça
            Se abertos = vazio então Fracasso := T;
            Senão
                N := Primeiro(abertos); {Pilha(topo)}
                Se N = solução então Sucesso := T;
                Senão
                    Enquanto R(N) <> vazio faça
                        Escolha r de R(N); New(u);
                        u := r(N); Insere(u, abertos);
                        Atualiza R(N);
                    Fim-enquanto;
                    Insere(N, fechados);
                Fim-se;
            Fim-se;
        Fim-enquanto;
    Fim.

Diferença em relação ao BFS: abertos é uma Pilha (FILO).
Os filhos são empilhados em ordem inversa à de ORDER para que o
primeiro filho (pela ORDER) fique no topo e seja processado primeiro.
Parâmetros extras:
  pruning=True  → descarta estados cujo estado já está em abertos ou fechados
                  (evita ciclos; não garante solução ótima)
  pruning=False → permite estados repetidos (árvore de busca "ingênua");
                  use max_depth para impedir explosão combinatória
  max_depth     → profundidade máxima de expansão (None = ilimitado)

A escolha de r em R(N) segue o parâmetro `order`:
  "asc"  → r1, r2, ..., r16  (padrão)
  "desc" → r16, r15, ..., r1
"""

from collections import deque

from utils import RULES, INITIAL_STATE, is_goal, apply_rule, show_board


# ── helpers ───────────────────────────────────────────────────────────────────

def state_key(state):
    """Representação hasheável do estado."""
    return tuple(state[sq] for sq in range(1, 10))
def applicable_rules(state, order="asc"):
    """Regras aplicáveis ao estado (precondição ok), em ordem crescente ou decrescente."""
    names = [
        rule
        for rule, (origin, dest) in RULES.items()
        if state[origin] is not None and state[dest] is None
    ]
    return list(reversed(names)) if order == "desc" else names
def _node_label(node_id, node_tree):
    """Etiqueta de um nó: sequência de regras da raiz até ele."""
    rules = []
    nid = node_id
    while node_tree[nid]["parent"] is not None:
        parent_id, rule = node_tree[nid]["parent"]
        rules.append(rule)
        nid = parent_id
    rules.reverse()
    if not rules:
        return "[raiz]"
    if len(rules) <= 4:
        return "[" + "→".join(rules) + "]"
    return "[" + "→".join(rules[:2]) + "→…→" + rules[-1] + "]"


def _levels_summary(node_ids, node_tree):
    """Conta nós por nível: 'nível 0: 1 nó, nível 1: 5 nós'."""
    from collections import Counter
    counts = Counter(node_tree[nid]["depth"] for nid in node_ids)
    if not counts:
        return "(vazio)"
    return ", ".join(
        f"nível {d}: {n} nó{'s' if n > 1 else ''}"
        for d, n in sorted(counts.items())
    )


def _print_nodelist(label, node_ids, node_tree, max_show=8):
    """Imprime lista de nós de forma compacta (topo da pilha primeiro)."""
    total = len(node_ids)
    if total == 0:
        print(f"  {label}: (vazio)")
        return
    summary = _levels_summary(node_ids, node_tree)
    print(f"  {label}: {total} nó{'s' if total > 1 else ''} [{summary}]")
    for nid in node_ids[:max_show]:
        n = node_tree[nid]
        print(f"    • nível {n['depth']}: {_node_label(nid, node_tree)}")
    if total > max_show:
        print(f"    … (+{total - max_show} não exibidos)")


def _solution_id_path(goal_id, node_tree):
    """Lista ordenada de IDs do caminho solução (raiz → meta)."""
    ids = []
    nid = goal_id
    while nid is not None:
        ids.append(nid)
        n = node_tree[nid]
        nid = n["parent"][0] if n["parent"] else None
    ids.reverse()
    return ids
# ── algoritmo principal ────────────────────────────────────────────────────────

def dfs(initial_state, order="asc", pruning=True, max_depth=None):
    """
    Busca em profundidade (DFS).

    pruning=True  → estados em abertos/fechados são descartados (poda)
    pruning=False → estados repetidos são permitidos; use max_depth para terminar
    max_depth     → profundidade máxima de expansão (None = ilimitado)
    Não garante solução ótima.

    Retorna (path, applied, stats, node_tree, trace, goal_id) ou None se falhar.

    node_tree : {node_id: {"state": dict, "depth": int,
                            "parent": (parent_id, rule) | None}}
    trace     : lista de dicts — um por iteração do laço principal:
                {"node_id", "depth", "rule",
                 "abertos_before", "fechados_before",
                 "children", "abertos_after", "fechados_after"}
    goal_id   : ID do nó meta no node_tree
    """
    _counter = [0]

    def new_id():
        i = _counter[0]
        _counter[0] += 1
        return i

    root_id = new_id()
    node_tree = {root_id: {"state": initial_state, "depth": 0, "parent": None}}
    opened = deque([root_id])       # abertos (Pilha de IDs — topo = direita)
    closed_ids: list[int] = []      # fechados (lista de IDs)
    seen_keys = {state_key(initial_state)} if pruning else set()

    stats = {"expanded": 0, "max_open": 1}
    trace = []
    success = failure = False
    goal_id = None

    while not (success or failure):
        if not opened:
            failure = True
            continue

        # Snapshot de abertos e fechados ANTES de retirar N
        abertos_snap = list(opened)
        fechados_snap = list(closed_ids)

        nid = opened.pop()              # N := Primeiro(abertos) {Pilha(topo)}
        N = node_tree[nid]
        if is_goal(N["state"]):         # N = solução → Sucesso
            success = True
            goal_id = nid
            continue

        if max_depth is not None and N["depth"] >= max_depth:
            closed_ids.append(nid)
            continue
        stats["expanded"] += 1
        children: list[tuple[int, str]] = []

        for rule in applicable_rules(N["state"], order=order):
            u_state = apply_rule(rule, N["state"])
            u_key = state_key(u_state)

            if pruning and u_key in seen_keys:    # poda: já visitado
                continue
            uid = new_id()
            node_tree[uid] = {
                "state": u_state,
                "depth": N["depth"] + 1,
                "parent": (nid, rule),
            }
            if pruning:
                seen_keys.add(u_key)

            children.append((uid, rule))
        # Empilha em ordem inversa para que o primeiro filho (por ORDER)
        # fique no topo da pilha e seja processado a seguir
        for uid, _ in reversed(children):
            opened.append(uid)

        closed_ids.append(nid)          # Insere(N, fechados)
        stats["max_open"] = max(stats["max_open"], len(opened))

        trace.append({
            "node_id": nid,
            "depth": N["depth"],
            "rule": N["parent"][1] if N["parent"] else None,
            "children": children,
            "abertos_before": abertos_snap,   # topo = último elemento
            "fechados_before": fechados_snap,
            "abertos_after": list(opened),
            "fechados_after": list(closed_ids),
        })
    if not success:
        if pruning:
            return None   # busca exaustiva sem solução → fracasso real
        # poda=False com max_depth: retorna a árvore explorada mesmo sem solução
        # (útil para visualizar a estrutura sem poda)
        return None, None, stats, node_tree, trace, None

    # Reconstrói caminho solução
    path, applied = [], []
    nid = goal_id
    while nid is not None:
        n = node_tree[nid]
        path.append(n["state"])
        if n["parent"] is not None:
            parent_id, rule = n["parent"]
            applied.append(rule)
            nid = parent_id
        else:
            nid = None
    path.reverse()
    applied.reverse()

    return path, applied, stats, node_tree, trace, goal_id


# ── exibição do caminho solução ────────────────────────────────────────────────

def print_solution(path, applied, node_tree, trace, goal_id, order="asc"):
    """
    Imprime o caminho solução com, a cada passo:
      - Nível (profundidade) do nó
      - Estado de Abertos e Fechados quando o nó pai foi expandido
      - Regras possíveis e a regra aplicada
      - Tabuleiro resultante
    """
    sol_ids = _solution_id_path(goal_id, node_tree)
    trace_by_id = {t["node_id"]: t for t in trace}

    print("\nEstado inicial [Nível 0]:")
    show_board(path[0])
    for i, rule in enumerate(applied):
        possibilities = applicable_rules(path[i], order=order)
        origin, dest = RULES[rule]
        level = i + 1

        print(f"\n{'─'*60}")
        print(f"Passo {i + 1}  [Nível {level}]  {rule}  ({origin} → {dest})")
        print(f"  possibilidades: "
              f"{', '.join(possibilities) if possibilities else '(nenhuma)'}")
        # Abertos/Fechados quando o nó pai (sol_ids[i]) foi expandido
        parent_id = sol_ids[i]
        if parent_id in trace_by_id:
            t = trace_by_id[parent_id]
            print()
            _print_nodelist("Abertos  (ao expandir nó pai, topo→base)", t["abertos_before"], node_tree)
            _print_nodelist("Fechados (ao expandir nó pai)", t["fechados_before"], node_tree)

        print(f"\n  → aplica {rule}")
        show_board(path[i + 1])
    print(f"\n{'─'*60}")
    print(f"Solução encontrada! [Nível {len(applied)}]")
    if trace:
        last_t = trace[-1]
        print()
        _print_nodelist("Abertos  (ao encontrar solução, topo→base)", last_t["abertos_after"], node_tree)
        _print_nodelist("Fechados (ao encontrar solução)", last_t["fechados_after"], node_tree)


# ── rastreio completo ──────────────────────────────────────────────────────────
def print_trace(trace, node_tree, goal_id, max_iterations=None):
    """
    Imprime o rastreio completo da DFS: a cada iteração mostra N, Abertos e
    Fechados. Nós no caminho solução são marcados com ★.

    max_iterations : exibe só as primeiras N iterações (None = todas)
    """
    sol_ids = set(_solution_id_path(goal_id, node_tree)) if goal_id is not None else set()
    total = len(trace)
    shown = trace if max_iterations is None else trace[:max_iterations]

    print(f"\n{'═'*70}")
    print(f"RASTREIO DFS — {total} iterações no total")
    if max_iterations is not None and max_iterations < total:
        print(f"(exibindo apenas as primeiras {max_iterations})")
    print(f"{'═'*70}")

    for k, t in enumerate(shown, 1):
        nid = t["node_id"]
        marker = " ★" if nid in sol_ids else ""
        label = _node_label(nid, node_tree)

        print(f"\nIteração {k}{marker}  |  N = nível {t['depth']}  {label}")
        _print_nodelist("  Abertos (antes, topo→base)", t["abertos_before"], node_tree, max_show=6)
        _print_nodelist("  Fechados (antes)", t["fechados_before"], node_tree, max_show=6)

        if t["children"]:
            child_labels = [
                f"{_node_label(uid, node_tree)} (via {r})"
                for uid, r in t["children"]
            ]
            print(f"  Gerou {len(t['children'])} filho(s): {', '.join(child_labels)}")
        else:
            print("  Sem filhos (nó folha ou limite de profundidade)")

        _print_nodelist("  Abertos (depois, topo→base)", t["abertos_after"], node_tree, max_show=6)
        _print_nodelist("  Fechados (depois)", t["fechados_after"], node_tree, max_show=6)
# ── visualização da árvore ─────────────────────────────────────────────────────

def plot_tree(path, node_tree, goal_id, order="asc", pruning=True, figsize=(22, 14)):
    """
    Plota a árvore de busca DFS com matplotlib + networkx.

    Usa node_id como identificador dos nós (funciona com pruning=True e pruning=False).
    Nós do caminho solução são destacados em laranja.
    Quando goal_id=None (sem solução encontrada), exibe apenas a árvore explorada.
    """
    import matplotlib.pyplot as plt
    import networkx as nx

    sol_id_path = _solution_id_path(goal_id, node_tree) if goal_id is not None else []
    sol_ids = set(sol_id_path)

    G = nx.DiGraph()
    depth = {}
    for nid, n in node_tree.items():
        G.add_node(nid)
        depth[nid] = n["depth"]
        if n["parent"] is not None:
            parent_id, rule = n["parent"]
            G.add_edge(parent_id, nid, rule=rule)

    # Layout hierárquico por nível
    levels: dict[int, list[int]] = {}
    for nid, d in depth.items():
        levels.setdefault(d, []).append(nid)
    pos = {}
    for d, nodes in levels.items():
        for i, nid in enumerate(nodes):
            pos[nid] = (i - len(nodes) / 2, -d)

    node_colors = ["#F4A261" if nid in sol_ids else "#AED6F1" for nid in G.nodes()]
    node_sizes  = [500 if nid in sol_ids else 200 for nid in G.nodes()]

    fig, ax = plt.subplots(figsize=figsize)
    nx.draw_networkx_nodes(G, pos, node_color=node_colors, node_size=node_sizes, ax=ax)
    nx.draw_networkx_edges(G, pos, arrows=True, arrowsize=10,
                           edge_color="#888888", ax=ax)

    # Rótulos só nas arestas do caminho solução
    sol_edges = set(zip(sol_id_path[:-1], sol_id_path[1:]))
    edge_labels = {
        (u, v): d["rule"]
        for u, v, d in G.edges(data=True)
        if (u, v) in sol_edges
    }
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels,
                                 font_size=7, ax=ax)

    from matplotlib.patches import Patch
    pruning_str = "com poda" if pruning else "sem poda"
    legend = [
        Patch(facecolor="#F4A261", label="Caminho solução"),
        Patch(facecolor="#AED6F1", label="Outros nós explorados"),
    ]
    ax.legend(handles=legend, loc="upper right")
    max_d = max(depth.values()) if depth else 0
    sol_depth = len(path) - 1 if path else "—"
    ax.set_title(
        f"Árvore DFS ({pruning_str}) — {len(G.nodes())} nós, "
        f"prof. máx. {max_d}, solução em prof. {sol_depth}",
        fontsize=12,
    )
    ax.axis("off")
    plt.tight_layout()
    plt.show()
if __name__ == "__main__":
    result = dfs(INITIAL_STATE)
    if result is None:
        print("Fracasso: abertos esvaziou sem encontrar solução.")
    else:
        path, applied, stats, node_tree, trace, goal_id = result
        print(f"Sucesso! Solução com {len(applied)} movimentos "
              f"({stats['expanded']} nós expandidos, "
              f"máx. de abertos = {stats['max_open']}):")
        print(" -> ".join(applied))
        print_solution(path, applied, node_tree, trace, goal_id)
