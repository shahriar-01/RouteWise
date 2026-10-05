import math

def calculate_financial(shipment_data, selected_route, incident_type, feasible_options=None):
    def to_float(v):
        if v is None:
            return 0
        s = str(v).replace(",", "").strip()
        return float(s) if s else 0

    try:
        cargo_value = float(str(shipment_data.get('cargo_value_bdt', 0)).replace(",", "").strip() or 0)
    except:
        cargo_value = 0
    try:
        original_cost = float(str(shipment_data.get('original_cost_bdt', 0)).replace(",", "").strip() or 0)
    except:
        original_cost = 0
    try:
        deadline = float(str(shipment_data.get('delivery_deadline_days', 0)).replace(",", "").strip() or 0)
    except:
        deadline = 0

    revenue = to_float(shipment_data.get('total_payment_received_bdt') or shipment_data.get('total_payment_bdt') or shipment_data.get('revenue_bdt', 0))
    if revenue == 0:
        revenue = round(cargo_value * 1.25, 2)
    else:
        revenue = round(revenue, 2)

    route = selected_route.get('selected_route', selected_route) if isinstance(selected_route.get('selected_route', None), dict) else selected_route

    recovery_cost = 0
    for k in ['total_cost', 'cost', 'recovery_cost', 'estimated_cost_bdt']:
        if k in route and route[k] not in (None, ''):
            try:
                recovery_cost = float(str(route[k]).replace(",", "").strip() or 0)
                break
            except:
                continue

    delivery_days = 0
    raw = None
    for k in ['total_time', 'time', 'estimated_time_days', 'delivery_time']:
        if k in route and route[k] not in (None, ''):
            raw = route[k]
            break
    if raw is not None:
        try:
            val = float(str(raw).replace(",", "").strip() or 0)
            delivery_days = val / 24.0 if ('total_time' in route or 'time' in route) else val
        except:
            delivery_days = 0

    ceil_days = math.ceil(delivery_days) if delivery_days > 0 else 0

    damage_cost = round(cargo_value * 0.02, 2) if incident_type and "cargo damaged" in str(incident_type).lower() else 0

    if ceil_days > deadline:
        delay_penalty = round((ceil_days - deadline) * 5000, 2)
    elif delivery_days > deadline:
        delay_penalty = round(math.ceil(delivery_days - deadline) * 5000, 2)
    else:
        delay_penalty = 0

    final_profit = round(revenue - original_cost - recovery_cost - damage_cost - delay_penalty, 2)
    profit_status = "Profit" if final_profit >= 0 else "Loss"

    try:
        budget = float(str(shipment_data.get('recovery_budget_bdt', 0)).replace(",", "").strip() or 0)
    except:
        budget = 0

    budget_exceeds = budget > revenue if revenue > 0 else False
    recovery_exceeds = recovery_cost > revenue if revenue > 0 else False

    comparison = []
    if feasible_options:
        for opt in feasible_options:
            try:
                oc = float(str(opt.get('estimated_cost_bdt', 0)).replace(",", "").strip() or 0)
            except:
                oc = 0
            try:
                ot = float(str(opt.get('estimated_time_days', 0)).replace(",", "").strip() or 0)
            except:
                ot = 0
            od = damage_cost
            op_delay = round((ot - deadline) * 5000, 2) if ot > deadline else 0
            op_profit = round(revenue - original_cost - oc - od - op_delay, 2)
            comparison.append({
                "option_id": opt.get('option_id'),
                "vehicle_id": opt.get('vehicle_id'),
                "route_description": opt.get('route_description'),
                "estimated_cost_bdt": oc,
                "estimated_time_days": ot,
                "risk_level": opt.get('risk_level'),
                "damage_cost": od,
                "delay_penalty": op_delay,
                "final_profit": op_profit,
                "profit": op_profit,
                "exceeds_payment": oc > revenue if revenue else False
            })

    sorted_comp = sorted(comparison, key=lambda x: x.get('final_profit', 0), reverse=True) if comparison else []

    return {
        "revenue": revenue, "total_payment_received": revenue, "total_payment": revenue,
        "original_cost": original_cost, "recovery_cost": recovery_cost,
        "damage_cost": damage_cost, "delay_penalty": delay_penalty,
        "final_profit": final_profit, "profit": final_profit,
        "delivery_time_days": round(delivery_days, 2), "delivery_days_ceiled": ceil_days,
        "deadline_days": deadline, "cargo_value": cargo_value,
        "incident_type": incident_type,
        "comparison": comparison, "comparison_sorted": sorted_comp, "feasible_comparison": comparison,
        "budget_exceeds_payment": budget_exceeds, "recovery_exceeds_payment": recovery_exceeds,
        "recovery_budget": budget, "recovery_budget_bdt": budget,
        "total_payment_received_bdt": revenue,
        "profit_status": profit_status, "status": profit_status,
        "breakdown": {
            "Revenue (Total Payment)": revenue, "Original Cost": original_cost,
            "Recovery Cost": recovery_cost, "Damage Cost": damage_cost,
            "Delay Penalty": delay_penalty, "Final Profit": final_profit
        }
    }
