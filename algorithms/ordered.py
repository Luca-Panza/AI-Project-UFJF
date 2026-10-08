"""Busca Ordenada (custo uniforme) para o problema dos 4 cavalos (tabuleiro 3x3).

Implementação fiel ao pseudocódigo do Algoritmo Básico de Busca, com
abertos como Fila ORDENADA PELO MENOR CUSTO acumulado (Busca Ordenada):

    Algoritmo Básico de Busca
    Início
        Defina(abertos); S := raiz; Fracasso := F; Sucesso := F;
        Insere(S, abertos); Defina(fechados);
        Enquanto não (Sucesso ou Fracasso) faça
            Se abertos = vazio então Fracasso := T;
            Senão
                N := Primeiro(abertos); {Fila ordenada: nó de MENOR CUSTO}
                Se N = solução então Sucesso := T;
                Senão
                    Enquanto R(N) <> vazio faça
                        Escolha r de R(N); New(u);
                        u := r(N); custo(u) := custo(N) + custo(r);
                        Insere(u, abertos) ordenado por custo;
                        Atualiza R(N);
                    Fim-enquanto;
                    Insere(N, fechados);
                Fim-se;
            Fim-se;
        Fim-enquanto;
    Fim.

Regras de ordenação de abertos:
  - abertos é sempre ordenada pelo custo acumulado g (raiz → nó);
  - em empate de custo, o nó gerado primeiro fica na frente;
  - o critério de desempate `order` só decide a ordem entre filhos do MESMO
    pai com o mesmo custo ("asc" → r1 antes de r2; "desc" → o contrário);
  - o teste de objetivo é feito quando o nó VIRA estado atual (sai de
    abertos), nunca ao ser gerado. Isso garante a solução de MENOR CUSTO.

Parâmetros extras:
  cost       → nome da função de custo em utils.COST_FUNCTIONS
               ("direcao" ou "destino") ou um callable (rule, state) → int
  pruning=True  → técnica de poda pelo vetor de menor custo.
                  Estado repetido com custo >= ao já registrado é podado;
                  com custo menor, substitui o nó antigo em abertos.
  pruning=False → permite estados repetidos; use max_depth para terminar
  max_depth  → profundidade máxima de expansão (None = ilimitado)
"""

from utils import RULES, INITIAL_STATE, COST_FUNCTIONS, is_goal, apply_rule, show_board


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
    """Etiqueta de um nó: sequência de regras da raiz até ele + custo acumulado."""
    rules = []
    nid = node_id
    while node_tree[nid]["parent"] is not None:
        parent_id, rule = node_tree[nid]["parent"]
        rules.append(rule)
        nid = parent_id
    rules.reverse()
    g = node_tree[node_id]["cost"]
    if not rules:
        return f"[raiz] (g={g})"
    if len(rules) <= 4:
        return "[" + "→".join(rules) + f"] (g={g})"
    return "[" + "→".join(rules[:2]) + "→…→" + rules[-1] + f"] (g={g})"


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
    """Imprime lista de nós de forma compacta (abertos: menor custo primeiro)."""
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

def ordered(initial_state, cost="direcao", order="asc", pruning=True, max_depth=None):
    """
    Busca Ordenada (custo uniforme).

    cost          → "direcao" | "destino" | callable(rule, state) → int
    order         → desempate entre filhos do mesmo pai com o mesmo custo
    pruning=True  → poda pelo vetor de menor custo (padrão)
    pruning=False → estados repetidos são permitidos; use max_depth para terminar
    max_depth     → profundidade máxima de expansão (None = ilimitado)

    Retorna (path, applied, stats, node_tree, trace, goal_id) ou None se falhar.

    node_tree : {node_id: {"state": dict, "depth": int, "cost": int,
                            "parent": (parent_id, rule) | None,
                            "pruned": bool (só quando substituído pela poda)}}
    trace     : lista de dicts — um por iteração do laço principal:
                {"node_id", "depth", "cost", "rule",
                 "abertos_before", "fechados_before",
                 "children", "pruned", "abertos_after", "fechados_after"}
    goal_id   : ID do nó meta no node_tree
    """
    cost_fn = COST_FUNCTIONS[cost] if isinstance(cost, str) else cost

    _counter = [0]

    def new_id():
        i = _counter[0]
        _counter[0] += 1
        return i

    root_id = new_id()
    node_tree = {root_id: {"state": initial_state, "depth": 0, "cost": 0, "parent": None}}

    opened: list[int] = [root_id]   # abertos (lista de IDs ordenada por custo)
    closed_ids: list[int] = []      # fechados (lista de IDs)
    # vetor de menor custo: state_key → node_id com o menor custo conhecido
    best: dict = {state_key(initial_state): root_id} if pruning else {}

    stats = {"expanded": 0, "max_open": 1, "cost": None}
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

        nid = opened.pop(0)             # N := Primeiro(abertos) (menor custo)
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
        pruned: list[tuple[str, int]] = []      # (regra, custo) descartados pela poda

        for rule in applicable_rules(N["state"], order=order):
            u_state = apply_rule(rule, N["state"])
            u_cost = N["cost"] + cost_fn(rule, N["state"])
            u_key = state_key(u_state)

            if pruning and u_key in best:
                old_id = best[u_key]
                if u_cost >= node_tree[old_id]["cost"]:
                    pruned.append((rule, u_cost))   # poda: já existe caminho igual ou melhor
                    continue
                # caminho mais barato: remove o nó antigo de abertos e da árvore
                if old_id in opened:
                    opened.remove(old_id)
                node_tree[old_id]["pruned"] = True

            uid = new_id()
            node_tree[uid] = {
                "state": u_state,
                "depth": N["depth"] + 1,
                "cost": u_cost,
                "parent": (nid, rule),
            }
            if pruning:
                best[u_key] = uid

            opened.append(uid)
            children.append((uid, rule))

        # Reordena abertos pelo custo; sort é estável, logo em empate o nó
        # gerado primeiro continua na frente.
        opened.sort(key=lambda i: node_tree[i]["cost"])

        closed_ids.append(nid)          # Insere(N, fechados)
        stats["max_open"] = max(stats["max_open"], len(opened))

        trace.append({
            "node_id": nid,
            "depth": N["depth"],
            "cost": N["cost"],
            "rule": N["parent"][1] if N["parent"] else None,
            "children": children,
            "pruned": pruned,
            "abertos_before": abertos_snap,   # inclui nid como 1.º elemento
            "fechados_before": fechados_snap,
            "abertos_after": list(opened),
            "fechados_after": list(closed_ids),
        })

    if not success:
        if pruning:
            return None   # busca exaustiva sem solução → fracasso real
        # pruning=False com max_depth: retorna a árvore explorada mesmo sem solução
        return None, None, stats, node_tree, trace, None

    stats["cost"] = node_tree[goal_id]["cost"]

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

def print_solution(path, applied, node_tree, trace, goal_id, cost="direcao", order="asc"):
    """
    Imprime o caminho solução com, a cada passo:
      - Nível (profundidade) e custo acumulado do nó
      - Estado de Abertos e Fechados quando o nó pai foi expandido
      - Regras possíveis (com custo) e a regra aplicada
      - Tabuleiro resultante
    """
    cost_fn = COST_FUNCTIONS[cost] if isinstance(cost, str) else cost
    sol_ids = _solution_id_path(goal_id, node_tree)
    trace_by_id = {t["node_id"]: t for t in trace}

    print("\nEstado inicial [Nível 0, g=0]:")
    show_board(path[0])

    for i, rule in enumerate(applied):
        possibilities = applicable_rules(path[i], order=order)
        origin, dest = RULES[rule]
        step_cost = cost_fn(rule, path[i])
        g = node_tree[sol_ids[i + 1]]["cost"]
        level = i + 1

        print(f"\n{'─'*60}")
        print(f"Passo {i + 1}  [Nível {level}, g={g}]  {rule}  ({origin} → {dest}, custo {step_cost})")
        poss_str = ", ".join(f"{r}({cost_fn(r, path[i])})" for r in possibilities)
        print(f"  possibilidades (custo): {poss_str if poss_str else '(nenhuma)'}")

        # Abertos/Fechados quando o nó pai (sol_ids[i]) foi expandido
        parent_id = sol_ids[i]
        if parent_id in trace_by_id:
            t = trace_by_id[parent_id]
            print()
            _print_nodelist("Abertos  (ao expandir nó pai)", t["abertos_before"], node_tree)
            _print_nodelist("Fechados (ao expandir nó pai)", t["fechados_before"], node_tree)

        print(f"\n  → aplica {rule}")
        show_board(path[i + 1])

    print(f"\n{'─'*60}")
    print(f"Solução encontrada! [Nível {len(applied)}, custo total {node_tree[goal_id]['cost']}]")
    if trace:
        last_t = trace[-1]
        print()
        _print_nodelist("Abertos  (ao encontrar solução)", last_t["abertos_after"], node_tree)
        _print_nodelist("Fechados (ao encontrar solução)", last_t["fechados_after"], node_tree)


# ── rastreio completo ──────────────────────────────────────────────────────────

def print_trace(trace, node_tree, goal_id, max_iterations=None):
    """
    Imprime o rastreio completo da Busca Ordenada: a cada iteração mostra N,
    Abertos e Fechados. Nós no caminho solução são marcados com ★.

    max_iterations : exibe só as primeiras N iterações (None = todas)
    """
    sol_ids = set(_solution_id_path(goal_id, node_tree)) if goal_id is not None else set()
    total = len(trace)
    shown = trace if max_iterations is None else trace[:max_iterations]

    print(f"\n{'═'*70}")
    print(f"RASTREIO BUSCA ORDENADA — {total} iterações no total")
    if max_iterations is not None and max_iterations < total:
        print(f"(exibindo apenas as primeiras {max_iterations})")
    print(f"{'═'*70}")

    for k, t in enumerate(shown, 1):
        nid = t["node_id"]
        marker = " ★" if nid in sol_ids else ""
        label = _node_label(nid, node_tree)

        print(f"\nIteração {k}{marker}  |  N = nível {t['depth']}  {label}")
        _print_nodelist("  Abertos (antes)", t["abertos_before"], node_tree, max_show=6)
        _print_nodelist("  Fechados (antes)", t["fechados_before"], node_tree, max_show=6)

        if t["children"]:
            child_labels = [
                f"{_node_label(uid, node_tree)} (via {r})"
                for uid, r in t["children"]
            ]
            print(f"  Gerou {len(t['children'])} filho(s): {', '.join(child_labels)}")
        else:
            print("  Sem filhos (nó folha ou limite de profundidade)")
        if t["pruned"]:
            print(f"  Podados: {', '.join(f'{r} (g={g})' for r, g in t['pruned'])}")

        _print_nodelist("  Abertos (depois)", t["abertos_after"], node_tree, max_show=6)
        _print_nodelist("  Fechados (depois)", t["fechados_after"], node_tree, max_show=6)


# ── visualização da árvore ─────────────────────────────────────────────────────

def plot_tree(path, node_tree, goal_id, cost="direcao", pruning=True, figsize=(22, 14)):
    """
    Plota a árvore de busca da Busca Ordenada com matplotlib + networkx.

    Usa node_id como identificador dos nós (funciona com pruning=True e pruning=False).
    Nós do caminho solução são destacados em laranja; nós substituídos pela poda
    (caminho mais barato encontrado depois) aparecem em cinza.
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

    def _color(nid):
        if nid in sol_ids:
            return "#F4A261"
        if node_tree[nid].get("pruned"):
            return "#D5D8DC"
        return "#AED6F1"

    node_colors = [_color(nid) for nid in G.nodes()]
    node_sizes  = [500 if nid in sol_ids else 200 for nid in G.nodes()]

    fig, ax = plt.subplots(figsize=figsize)
    nx.draw_networkx_nodes(G, pos, node_color=node_colors, node_size=node_sizes, ax=ax)
    nx.draw_networkx_edges(G, pos, arrows=True, arrowsize=10,
                           edge_color="#888888", ax=ax)

    # Rótulos (regra + custo acumulado) só nas arestas do caminho solução
    sol_edges = set(zip(sol_id_path[:-1], sol_id_path[1:]))
    edge_labels = {
        (u, v): f"{d['rule']} (g={node_tree[v]['cost']})"
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
        Patch(facecolor="#D5D8DC", label="Substituídos pela poda"),
    ]
    ax.legend(handles=legend, loc="upper right")
    max_d = max(depth.values()) if depth else 0
    sol_depth = len(path) - 1 if path else "—"
    sol_cost = node_tree[goal_id]["cost"] if goal_id is not None else "—"
    cost_name = cost if isinstance(cost, str) else getattr(cost, "__name__", "custom")
    ax.set_title(
        f"Árvore Busca Ordenada (custo={cost_name!r}, {pruning_str}) — {len(G.nodes())} nós, "
        f"prof. máx. {max_d}, solução em prof. {sol_depth} com custo {sol_cost}",
        fontsize=12,
    )
    ax.axis("off")
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    result = ordered(INITIAL_STATE)
    if result is None:
        print("Fracasso: abertos esvaziou sem encontrar solução.")
    else:
        path, applied, stats, node_tree, trace, goal_id = result
        print(f"Sucesso! Solução com {len(applied)} movimentos e custo {stats['cost']} "
              f"({stats['expanded']} nós expandidos, "
              f"máx. de abertos = {stats['max_open']}):")
        print(" -> ".join(applied))
        print_solution(path, applied, node_tree, trace, goal_id)
