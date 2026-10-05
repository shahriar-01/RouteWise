def compile_evaluation(csp_result, dijkstra_result, astar_result, hill_result):
    def get(d, k, default=0):
        if isinstance(d, dict):
            return d.get(k, default)
        return default

    if isinstance(csp_result, dict):
        m = csp_result.get('metrics', {})
        if not m:
            m = {
                "total_checked": get(csp_result, 'total_checked', get(csp_result, 'options_checked', 0)),
                "removed": get(csp_result, 'removed', get(csp_result, 'options_removed', 0)),
                "passed": get(csp_result, 'passed', get(csp_result, 'options_passed', 0)),
                "execution_time_ms": get(csp_result, 'execution_time_ms', 0)
            }
        csp_time = float(m.get('execution_time_ms', get(csp_result, 'execution_time_ms', 0)) or 0)
        csp_checked = int(m.get('total_checked', m.get('options_checked', 0)) or 0)
        csp_removed = int(m.get('removed', m.get('options_removed', 0)) or 0)
        csp_passed = int(m.get('passed', m.get('options_passed', 0)) or 0)
    else:
        csp_time = csp_checked = csp_removed = csp_passed = 0

    dij_time = float(get(dijkstra_result, 'execution_time_ms', 0) or 0)
    dij_nodes = len(get(dijkstra_result, 'nodes_explored', [])) if isinstance(get(dijkstra_result, 'nodes_explored', []), list) else get(dijkstra_result, 'nodes_explored_count', 0)
    dij_path = get(dijkstra_result, 'path', [])

    ast_time = float(get(astar_result, 'execution_time_ms', 0) or 0)
    ast_nodes = len(get(astar_result, 'nodes_explored', [])) if isinstance(get(astar_result, 'nodes_explored', []), list) else get(astar_result, 'nodes_explored_count', 0)
    ast_path = get(astar_result, 'path', [])

    hill_time = float(get(hill_result, 'execution_time_ms', 0) or 0)
    hill_choice = get(hill_result, 'selected', get(hill_result, 'decision', 'Unknown'))

    total = round(csp_time + dij_time + ast_time + hill_time, 3)

    if dij_nodes > 0:
        diff = dij_nodes - ast_nodes
        pct = round((diff / dij_nodes * 100) if dij_nodes else 0, 1)
        eff = {
            "dijkstra_nodes": dij_nodes, "astar_nodes": ast_nodes,
            "difference": diff, "reduction_percent": pct,
            "more_efficient": "A*" if ast_nodes < dij_nodes else ("Dijkstra" if dij_nodes < ast_nodes else "Equal"),
            "explanation": f"A* explored {ast_nodes} vs Dijkstra {dij_nodes}, reduced by {pct}%." if ast_nodes < dij_nodes else "Both explored similar nodes."
        }
    else:
        eff = {"dijkstra_nodes": dij_nodes, "astar_nodes": ast_nodes, "difference": 0, "reduction_percent": 0, "more_efficient": "Equal"}

    return {
        "csp": {"execution_time_ms": csp_time, "total_checked": csp_checked, "options_checked": csp_checked, "removed": csp_removed, "options_removed": csp_removed, "passed": csp_passed, "options_passed": csp_passed},
        "csp_metrics": {"total_checked": csp_checked, "removed": csp_removed, "passed": csp_passed, "execution_time_ms": csp_time},
        "dijkstra": {"execution_time_ms": dij_time, "nodes_explored": dij_nodes, "nodes_explored_count": dij_nodes, "path": dij_path, "path_found": dij_path},
        "dijkstra_metrics": {"nodes_explored": dij_nodes, "execution_time_ms": dij_time, "path": dij_path},
        "astar": {"execution_time_ms": ast_time, "nodes_explored": ast_nodes, "nodes_explored_count": ast_nodes, "path": ast_path, "path_found": ast_path},
        "astar_metrics": {"nodes_explored": ast_nodes, "execution_time_ms": ast_time, "path": ast_path},
        "hill_climbing": {"execution_time_ms": hill_time, "candidates_compared": 2, "decision": hill_choice},
        "hill_metrics": {"execution_time_ms": hill_time, "candidates_compared": 2, "decision": hill_choice},
        "total_execution_time_ms": total, "total_time": total,
        "efficiency": eff, "all_algo_times": [csp_time, dij_time, ast_time, hill_time], "nodes_comparison": [dij_nodes, ast_nodes]
    }
