import csv
import json
import os
import time
from flask import Flask, render_template, request, session, redirect, url_for, jsonify

from algorithms.csp import run_csp
from algorithms.dijkstra import run_dijkstra
from algorithms.astar import run_astar
from algorithms.hill_climbing import run_hill_climbing
from modules.shipment import Shipment
from modules.incident import generate_recovery_options
from modules.financial import calculate_financial
from modules.evaluation import compile_evaluation

app = Flask(__name__)
app.secret_key = "routeWise-secret-key-2026-dhaka"

def load_csv(name):
    path = os.path.join(os.path.dirname(__file__), 'data', f'{name}.csv')
    rows = []
    with open(path, newline='', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            rows.append({k.strip(): (v.strip() if isinstance(v, str) else v) for k, v in row.items()})
    return rows

def load_routes():
    return load_csv('routes')

def load_vehicles():
    return load_csv('vehicles')

def load_locations():
    return load_csv('locations')

def parse_blocked_flag(value):
    if value is None:
        return 0
    if isinstance(value, bool):
        return 1 if value else 0
    if isinstance(value, (int, float)):
        return 1 if value != 0 else 0
    text = str(value).strip().lower()
    if text in ('', '0', 'false', 'no', 'n', 'off'):
        return 0
    if text in ('1', 'true', 'yes', 'y', 'on'):
        return 1
    try:
        return 1 if float(text) != 0 else 0
    except (TypeError, ValueError):
        return 0

def build_graph(routes, incident_type=None, origin=None, destination=None, locations=None):
    from collections import defaultdict
    country_map = {}
    if locations and origin and destination:
        for loc in locations:
            name = str(loc.get('location_name', '')).strip()
            country = str(loc.get('country', '')).strip()
            if not country:
                if name in ["Dhaka", "Khulna", "Chittagong"]:
                    country = "Bangladesh"
                elif name in ["Kolkata", "Port Blair"]:
                    country = "India"
                elif name == "Yangon":
                    country = "Myanmar"
                elif name == "Bangkok":
                    country = "Thailand"
                elif name == "Kuala Lumpur":
                    country = "Malaysia"
                elif name == "Singapore":
                    country = "Singapore"
                elif name == "Jakarta":
                    country = "Indonesia"
                else:
                    country = "Unknown"
            country_map[name] = country

    origin_country = country_map.get(str(origin).strip()) if country_map else None
    dest_country = country_map.get(str(destination).strip()) if country_map else None
    same_country = origin_country and dest_country and origin_country == dest_country

    graph = defaultdict(list)
    for r in routes:
        if parse_blocked_flag(r.get('blocked', '0')) == 1:
            continue
        frm = str(r.get('from', '')).strip()
        to = str(r.get('to', '')).strip()

        if same_country:
            if country_map.get(frm) != origin_country or country_map.get(to) != origin_country:
                continue

        if incident_type == "Road Blocked" and origin and destination:
            if frm == origin and to == destination:
                continue

        try:
            cost = float(r.get('cost_bdt', 0))
            ttime = float(r.get('travel_time_hrs', 0))
            dist = float(r.get('distance_km', 0))
        except:
            continue
        graph[frm].append((to, cost, ttime, dist, r.get('route_type', 'road')))
    return dict(graph)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/shipment', methods=['GET'])
def shipment():
    locs = [l['location_name'] for l in load_locations()]
    return render_template('shipment.html', locations=locs)

@app.route('/incident', methods=['POST'])
def incident():
    data = {
        'origin': request.form.get('origin', '').strip(),
        'destination': request.form.get('destination', '').strip(),
        'cargo_weight_tons': request.form.get('cargo_weight_tons', '').strip(),
        'cargo_value_bdt': request.form.get('cargo_value_bdt', '').strip(),
        'original_cost_bdt': request.form.get('original_cost_bdt', '').strip(),
        'total_payment_received_bdt': request.form.get('total_payment_received_bdt', '').strip(),
        'delivery_deadline_days': request.form.get('delivery_deadline_days', '').strip(),
        'transportation_type': request.form.get('transportation_type', '').strip(),
        'recovery_budget_bdt': request.form.get('recovery_budget_bdt', '').strip()
    }
    if data['origin'] == data['destination']:
        locs = [l['location_name'] for l in load_locations()]
        return render_template('shipment.html', locations=locs, error="Origin and destination must be different", shipment=data)
    try:
        s = Shipment(**data)
        data = s.to_dict()
    except Exception as e:
        locs = [l['location_name'] for l in load_locations()]
        return render_template('shipment.html', locations=locs, error=str(e), shipment=data)
    session['shipment'] = data
    return render_template('incident.html', shipment=data)

@app.route('/analyze', methods=['POST'])
def analyze():
    incident_type = request.form.get('incident_type', '').strip() or request.form.get('incident', '').strip()
    if not incident_type:
        return render_template('incident.html', shipment=session.get('shipment'), error="Please select an incident type")
    session['incident_type'] = incident_type
    return render_template('processing.html', shipment=session.get('shipment'), incident_type=incident_type)

@app.route('/run_analysis', methods=['POST'])
def run_analysis():
    try:
        shipment_data = session.get('shipment')
        incident_type = session.get('incident_type')
        if not shipment_data or not incident_type:
            return jsonify({"status": "error", "message": "Missing shipment or incident data"}), 400

        routes = load_routes()
        vehicles = load_vehicles()
        locations = load_locations()

        recovery_options = generate_recovery_options(incident_type, shipment_data, vehicles, routes)

        t0 = time.perf_counter()
        csp_result = run_csp(recovery_options, shipment_data, routes, vehicles)
        csp_time = round((time.perf_counter() - t0) * 1000, 3)

        if isinstance(csp_result, dict):
            feasible = csp_result.get('feasible_options', [])
            csp_metrics_raw = csp_result.get('metrics', {})
            csp_time_val = csp_result.get('execution_time_ms', csp_time)
            csp_log = csp_result.get('detailed_log', csp_result.get('log', []))
        else:
            feasible = csp_result[0] if len(csp_result) > 0 else []
            csp_log = csp_result[1] if len(csp_result) > 1 else []
            csp_time_val = csp_time
            csp_metrics_raw = {"total_checked": len(recovery_options), "removed": len(recovery_options)-len(feasible), "passed": len(feasible), "execution_time_ms": csp_time}

        if not feasible:
            total_payment = shipment_data.get('total_payment_received_bdt', 0)
            budget = shipment_data.get('recovery_budget_bdt', 0)
            try:
                total_payment = float(str(total_payment).replace(',', ''))
                budget = float(str(budget).replace(',', ''))
            except:
                pass
            warnings, recs = [], []
            if budget > total_payment and total_payment > 0:
                warnings.append(f"Recovery Budget (BDT {int(budget):,}) exceeds Total Payment Received (BDT {int(total_payment):,}).")
                recs.append(f"Reduce Recovery Budget to ≤ BDT {int(total_payment):,} or increase Total Payment. Try budget ≤ {int(total_payment*0.8):,} to leave profit margin.")
            if recovery_options:
                cheapest = min(recovery_options, key=lambda x: float(str(x.get('estimated_cost_bdt', 0)).replace(',', '') or 9e12) if str(x.get('estimated_cost_bdt', 0)).replace(',', '').replace('.','',1).isdigit() else 9e12)
                recs.append(f"Cheapest recovery option costs BDT {cheapest.get('estimated_cost_bdt', 'unknown')} — increase budget or choose lighter cargo. With 1000 routes, budget 30k-300k usually yields options.")
            recs.append("Try increasing Delivery Deadline, reducing Cargo Weight, or selecting Sea/Aircraft alternatives.")
            return jsonify({"status": "error", "message": "No feasible recovery options after CSP filtering.", "csp_log": csp_log, "warnings": warnings, "recommendations": recs}), 400

        origin = shipment_data.get('origin')
        destination = shipment_data.get('destination')
        graph = build_graph(routes, incident_type=incident_type, origin=origin, destination=destination, locations=locations)

        dijkstra_result = run_dijkstra(graph, origin, destination, locations)
        astar_result = run_astar(graph, origin, destination, locations)

        if not dijkstra_result.get('path') or not astar_result.get('path'):
            if not dijkstra_result.get('path') and astar_result.get('path'):
                dijkstra_result = astar_result
            elif not astar_result.get('path') and dijkstra_result.get('path'):
                astar_result = dijkstra_result
            else:
                return jsonify({"status": "error", "message": f"No route found between {origin} and {destination} for incident '{incident_type}'.", "recommendations": ["Select Sea or Aircraft for long distances", "Try Dhaka↔Chittagong, Khulna, or Singapore"]}), 400

        road_note = None
        if incident_type == "Road Blocked":
            orig_graph = build_graph(routes, locations=locations, origin=origin, destination=destination)
            has_direct = any(to == destination and rtype.lower() == 'road' for to, _, _, _, rtype in orig_graph.get(origin, []))
            if dijkstra_result.get('path') == [origin, destination]:
                road_note = f"Direct road {origin}→{destination} was blocked — alternative via intermediate hub was found: {' → '.join(dijkstra_result.get('path', []))}"
            else:
                road_note = f"Road Blocked incident — direct road {origin}→{destination} avoided. Alternative route: {' → '.join(dijkstra_result.get('path', []))} (vs direct road would be blocked)"

        hill_result = run_hill_climbing(dijkstra_result, astar_result, threshold=5)
        selected = hill_result.get('selected_route', {})
        selected_cost = selected.get('total_cost', selected.get('cost', 0))

        best_match = None
        min_diff = float('inf')
        for fo in feasible:
            try:
                ec = float(str(fo.get('estimated_cost_bdt', 0)).replace(',', ''))
            except:
                ec = 9e12
            diff = abs(ec - float(selected_cost))
            if diff < min_diff:
                min_diff, best_match = diff, fo

        risk = best_match.get('risk_level', 'Medium') if best_match else 'Medium'
        selected['risk_level'] = risk
        selected['route_description'] = " - ".join(selected.get('path', []))
        ttime = selected.get('total_time', selected.get('time', 0))
        days = round(ttime / 24.0, 2) if ttime else 0
        selected['delivery_time_days'] = days
        selected['estimated_time_days'] = days

        financial = calculate_financial(shipment_data, selected, incident_type, feasible)

        warnings, recommendations = [], []
        try:
            total_val = float(str(shipment_data.get('total_payment_received_bdt', 0)).replace(',', ''))
            budget_val = float(str(shipment_data.get('recovery_budget_bdt', 0)).replace(',', ''))
        except:
            total_val = budget_val = 0

        if financial.get('budget_exceeds_payment'):
            warnings.append(f"Recovery Budget (BDT {financial.get('recovery_budget_bdt', budget_val):,}) exceeds Total Payment Received (BDT {financial.get('revenue', total_val):,}) — violates Recovery Budget ≤ Total Payment rule.")
            recommendations.append(f"Reduce Recovery Budget to ≤ BDT {int(total_val):,} or increase Total Payment. Suggested budget ≤ {int(total_val*0.7):,} to keep profit.")
        if financial.get('recovery_exceeds_payment'):
            warnings.append(f"Recovery Cost (BDT {financial.get('recovery_cost',0):,}) exceeds Total Payment Received (BDT {financial.get('revenue',0):,}) — results in loss even if within budget.")
            recommendations.append("Choose cheaper recovery: Sea instead of Road for long distance, lighter cargo, or increase Total Payment. Cheapest is BDT " + f"{min([int(str(f.get('estimated_cost_bdt',0)).replace(',','') or 0) for f in feasible if str(f.get('estimated_cost_bdt',0)).replace(',','').isdigit()], default=0):,}.")
        if financial.get('profit_status') == "Loss":
            warnings.append(f"Final Profit is negative (BDT {financial.get('final_profit',0):,}) — operation at loss.")
            recommendations.append("To achieve profit: increase Total Payment (Revenue), negotiate lower Original Cost, or select lower Recovery Cost option.")
        if road_note:
            warnings.append(road_note)
        if budget_val > 0 and total_val > 0 and budget_val <= total_val and financial.get('recovery_cost',0) > budget_val:
            warnings.append(f"Recovery Cost BDT {financial.get('recovery_cost',0):,} exceeds Recovery Budget BDT {budget_val:,} — but within Total Payment. Budget is tight.")
            recommendations.append(f"Increase Recovery Budget up to Total Payment BDT {int(total_val):,} or pick cheaper feasible option.")

        evaluation = compile_evaluation(csp_result, dijkstra_result, astar_result, hill_result)

        csp_metrics = {
            "total_checked": csp_result.get('total_checked', csp_metrics_raw.get('total_checked', len(recovery_options))),
            "removed": csp_result.get('removed', csp_metrics_raw.get('removed', 0)),
            "passed": csp_result.get('passed', csp_metrics_raw.get('passed', len(feasible))),
            "execution_time_ms": csp_result.get('execution_time_ms', csp_time_val),
            "options_checked": csp_result.get('total_checked', len(recovery_options)),
            "options_removed": csp_result.get('removed', 0),
            "options_passed": csp_result.get('passed', len(feasible)),
            "detailed_log": csp_log
        }
        dij_metrics = {
            "nodes_explored": len(dijkstra_result.get('nodes_explored', [])),
            "nodes_explored_count": len(dijkstra_result.get('nodes_explored', [])),
            "execution_time_ms": dijkstra_result.get('execution_time_ms', 0),
            "path": dijkstra_result.get('path', []),
            "total_cost": dijkstra_result.get('total_cost', 0),
            "total_time": dijkstra_result.get('total_time', 0)
        }
        ast_metrics = {
            "nodes_explored": len(astar_result.get('nodes_explored', [])),
            "nodes_explored_count": len(astar_result.get('nodes_explored', [])),
            "execution_time_ms": astar_result.get('execution_time_ms', 0),
            "path": astar_result.get('path', []),
            "total_cost": astar_result.get('total_cost', 0),
            "total_time": astar_result.get('total_time', 0)
        }
        hill_metrics = {
            "execution_time_ms": hill_result.get('execution_time_ms', 0),
            "candidates_compared": 2,
            "decision": hill_result.get('selected', ''),
            "cost_difference": hill_result.get('cost_difference', 0),
            "percentage_difference": hill_result.get('percentage_difference', 0),
            "threshold": hill_result.get('threshold', 5),
            "threshold_percent": hill_result.get('threshold_percent', 5),
            "classification": hill_result.get('classification', ''),
            "reason": hill_result.get('reason', ''),
            "rule_applied": hill_result.get('rule_applied', hill_result.get('rule', '')),
            "signed_percentage": hill_result.get('signed_percentage', 0)
        }

        all_times = [csp_metrics["execution_time_ms"], dij_metrics["execution_time_ms"], ast_metrics["execution_time_ms"], hill_metrics["execution_time_ms"]]

        recommended = {
            "path": selected.get('path', []), "route_path": selected.get('path', []),
            "cost": selected.get('total_cost', selected.get('cost', 0)), "total_cost": selected.get('total_cost', selected.get('cost', 0)),
            "time": selected.get('total_time', 0), "total_time": selected.get('total_time', 0),
            "distance": selected.get('total_distance', 0), "total_distance": selected.get('total_distance', 0),
            "risk_level": risk, "selected_by": hill_result.get('selected', ''), "delivery_time_days": days, "route_description": " - ".join(selected.get('path', []))
        }
        dij_route = {
            "path": dijkstra_result.get('path', []), "cost": dijkstra_result.get('total_cost', 0), "total_cost": dijkstra_result.get('total_cost', 0),
            "time": dijkstra_result.get('total_time', 0), "total_time": dijkstra_result.get('total_time', 0), "distance": dijkstra_result.get('total_distance', 0),
            "nodes_explored": dijkstra_result.get('nodes_explored', []), "nodes_explored_count": len(dijkstra_result.get('nodes_explored', [])), "execution_time_ms": dijkstra_result.get('execution_time_ms', 0)
        }
        ast_route = {
            "path": astar_result.get('path', []), "cost": astar_result.get('total_cost', 0), "total_cost": astar_result.get('total_cost', 0),
            "time": astar_result.get('total_time', 0), "total_time": astar_result.get('total_time', 0), "distance": astar_result.get('total_distance', 0),
            "nodes_explored": astar_result.get('nodes_explored', []), "nodes_explored_count": len(astar_result.get('nodes_explored', [])), "execution_time_ms": astar_result.get('execution_time_ms', 0)
        }
        hill_decision = {
            "cost_difference": hill_result.get('cost_difference', 0), "percentage_difference": hill_result.get('percentage_difference', 0),
            "threshold": hill_result.get('threshold', 5), "threshold_percent": hill_result.get('threshold_percent', 5),
            "decision_type": hill_result.get('classification', ''), "classification": hill_result.get('classification', ''),
            "reason": hill_result.get('reason', ''), "selected": hill_result.get('selected', ''), "selected_route": selected,
            "rule_applied": hill_result.get('rule_applied', hill_result.get('rule', '')), "dijkstra_cost": hill_result.get('dijkstra_cost', 0), "astar_cost": hill_result.get('astar_cost', 0),
            "dijkstra_time": hill_result.get('dijkstra_time', 0), "astar_time": hill_result.get('astar_time', 0), "signed_percentage": hill_result.get('signed_percentage', 0)
        }

        results = {
            "recommended_route": recommended, "dijkstra_route": dij_route, "astar_route": ast_route,
            "hill_climbing_decision": hill_decision, "hill_result": hill_result,
            "csp_metrics": csp_metrics, "dijkstra_metrics": dij_metrics, "astar_metrics": ast_metrics, "hill_metrics": hill_metrics,
            "financial": financial, "feasible_options": feasible, "feasible_comparison": financial.get('comparison', []),
            "comparison_sorted": financial.get('comparison_sorted', financial.get('comparison', [])), "all_algo_times": all_times,
            "evaluation": evaluation, "shipment": shipment_data, "incident_type": incident_type,
            "csp_log": csp_log, "csp_detailed_log": csp_log, "total_execution_time_ms": evaluation.get('total_execution_time_ms', sum(all_times)),
            "warnings": warnings, "recommendations": recommendations
        }

        session['results'] = results
        return jsonify({"status": "complete", "results": results})

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/result', methods=['GET'])
def result():
    results = session.get('results')
    if not results:
        return redirect(url_for('index'))
    chart_data = {
        "algo_times": results.get('all_algo_times', [0,0,0,0]),
        "algo_labels": ["CSP", "Dijkstra", "A*", "Hill Climbing"],
        "nodes_explored": [results.get('dijkstra_metrics', {}).get('nodes_explored', 0), results.get('astar_metrics', {}).get('nodes_explored', 0)],
        "csp_filtered": [results.get('csp_metrics', {}).get('removed', 0), results.get('csp_metrics', {}).get('passed', 0)],
        "cost_comparison": [results.get('dijkstra_route', {}).get('cost', 0), results.get('astar_route', {}).get('cost', 0)],
        "time_comparison": [round(results.get('dijkstra_route', {}).get('time', 0)/24,2), round(results.get('astar_route', {}).get('time', 0)/24,2)]
    }
    return render_template('result.html', results=results, chart_data=json.dumps(chart_data), results_json=json.dumps(results))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
