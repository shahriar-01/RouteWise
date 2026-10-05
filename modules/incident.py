import random

def generate_recovery_options(incident_type, shipment_data, vehicles=None, routes=None):
    incident_type = str(incident_type).strip()
    origin = str(shipment_data.get('origin', 'Dhaka')).strip()
    dest = str(shipment_data.get('destination', 'Singapore')).strip()

    def _pf(v, d):
        if v is None:
            return d
        try:
            return float(str(v).replace(",", "").strip())
        except:
            return d

    deadline = _pf(shipment_data.get('delivery_deadline_days', 5), 5)
    budget = _pf(shipment_data.get('recovery_budget_bdt', 100000), 100000)
    weight = _pf(shipment_data.get('cargo_weight_tons', 8), 8)
    key = incident_type.lower().strip()

    def opt(oid, desc, vid, rdesc, cost, t, risk):
        return {
            "option_id": oid, "description": desc, "vehicle_id": vid,
            "route_description": rdesc, "estimated_cost_bdt": int(cost),
            "estimated_time_days": float(t), "risk_level": risk
        }

    def pick_vehicle(min_cap, preferred=None, fallback="V001"):
        if not vehicles:
            return fallback
        cands = []
        for v in vehicles:
            try:
                cap = float(str(v.get('capacity_tons', 0)).replace(",", "").strip() or 0)
            except:
                continue
            if str(v.get('available', '')).strip().lower() != 'yes' or cap < min_cap:
                continue
            if preferred:
                vtype = str(v.get('type', '')).lower()
                suit = str(v.get('suitable_for', '')).lower()
                if preferred == 'ship' and 'ship' not in vtype and 'sea' not in suit:
                    continue
                if preferred == 'air' and 'air' not in vtype and 'air' not in suit:
                    continue
                if preferred == 'road' and 'truck' not in vtype and 'van' not in vtype and 'road' not in suit:
                    continue
            cands.append((cap, v))
        if cands:
            cands.sort(key=lambda x: x[0])
            return cands[0][1].get('vehicle_id')
        any_cands = []
        for v in vehicles:
            try:
                cap = float(str(v.get('capacity_tons', 0)).replace(",", "").strip() or 0)
            except:
                continue
            if str(v.get('available', '')).strip().lower() == 'yes' and cap >= min_cap:
                any_cands.append((cap, v))
        if any_cands:
            any_cands.sort(key=lambda x: x[0])
            return any_cands[0][1].get('vehicle_id')
        return fallback

    def feasible_cost(ratio=0.6, min_c=12000, max_c=65000):
        if budget < 20000:
            c = int(budget * 0.80)
        elif budget < 40000:
            c = int(budget * 0.70)
        else:
            c = int(budget * ratio)
        c = max(min_c, min(c, max_c))
        if c > budget:
            c = int(budget * 0.90)
        c = max(8000, c)
        if c > budget:
            c = max(5000, int(budget) - 500)
        return c

    def feasible_time(off=1):
        t = deadline - off
        if t < 1:
            t = 1
        return float(t if t <= deadline else deadline)

    road_v = pick_vehicle(weight, 'road', "V001")
    ship_v = pick_vehicle(weight, 'ship', "V004")
    air_v = pick_vehicle(weight, 'air', "V015")
    any_v = pick_vehicle(weight, fallback="V014")

    options = []

    if "road blocked" in key:
        options.append(opt("RB-001", "Alternative road via Chittagong hub", road_v, f"{origin} - Chittagong - Kolkata - Yangon - Bangkok - {dest}", feasible_cost(0.60), feasible_time(1), "Low"))
        sv = ship_v if weight <= 80 else any_v
        if sv == "V001" and weight > 10:
            sv = pick_vehicle(weight, fallback="V016")
        options.append(opt("RB-002", "Sea/air hybrid via Kolkata and Yangon", sv, f"{origin} - Chittagong - Kolkata - Yangon - Bangkok - Kuala Lumpur - {dest}", feasible_cost(0.55), feasible_time(0.5 if deadline >= 2 else 0), "Medium"))
        options.append(opt("RB-003", "Small van via blocked direct road", "V006", f"{origin} - Khulna - Kolkata - Bangkok - {dest}", 45000, 2, "Medium"))
        options.append(opt("RB-004", "Unavailable heavy truck", "V003", f"{origin} - Kolkata - Port Blair - Bangkok - {dest}", 75000, 3, "Low"))
        options.append(opt("RB-005", "Direct cheapest through blocked segment", "V008", f"{origin} - Kolkata - Bangkok - {dest}", 40000, 4, "High"))
        options.append(opt("RB-006", "Ultra-fast air premium", air_v, f"{origin} - Dhaka - Singapore", int(budget + 50000), 1, "Low"))
        options.append(opt("RB-007", "Budget saver via Ship through Port Blair", ship_v, f"{origin} - Port Blair - Singapore - {dest}", feasible_cost(0.45, 8000, 40000), feasible_time(1.5), "Medium"))

    elif "vehicle unavailable" in key:
        v1 = pick_vehicle(weight, 'road', "V005")
        v2 = pick_vehicle(weight, fallback="V016")
        options.append(opt("VU-001", "Replace with Truck via Khulna", v1, f"{origin} - Khulna - Kolkata - Yangon - Bangkok - {dest}", feasible_cost(0.60), feasible_time(1), "Low"))
        options.append(opt("VU-002", "Replace with Truck via Chittagong", v2, f"{origin} - Chittagong - Kolkata - Yangon - Bangkok - {dest}", feasible_cost(0.52), feasible_time(0.8), "Medium"))
        options.append(opt("VU-003", "Reuse unavailable Ship V007", "V007", f"{origin} - Chittagong - Port Blair - Singapore - {dest}", 68000, 5, "High"))
        options.append(opt("VU-004", "Small van will fail for heavy cargo", "V006", f"{origin} - Kolkata - Bangkok - {dest}", 38000, 3, "High"))
        options.append(opt("VU-005", "Heavy Truck V011 fast but expensive", "V011", f"{origin} - Bangkok - Kuala Lumpur - {dest}", int(budget + 40000), 2, "Medium"))
        options.append(opt("VU-006", "Delayed Ship V010 slow but cheap", "V010", f"{origin} - Chittagong - Kolkata - Yangon - Bangkok - {dest}", 48000, deadline + 3, "Medium"))
        options.append(opt("VU-007", "Air alternative via Aircraft", pick_vehicle(weight, 'air', "V015"), f"{origin} - Dhaka - Singapore - {dest}", feasible_cost(0.75, 15000, 90000), 1, "Low"))

    elif "port unavailable" in key:
        v1 = pick_vehicle(weight, 'road', "V001")
        options.append(opt("PU-001", "Bypass port via road through Khulna", v1, f"{origin} - Khulna - Kolkata - Yangon - Bangkok - Kuala Lumpur - {dest}", feasible_cost(0.62), feasible_time(1.2), "Medium"))
        options.append(opt("PU-002", "Alternative sea via Yangon and Kuala Lumpur", ship_v, f"{origin} - Yangon - Bangkok - Kuala Lumpur - {dest}", feasible_cost(0.58), feasible_time(1), "Low"))
        options.append(opt("PU-003", "Small van via blocked Kolkata-Bangkok", "V002", f"{origin} - Kolkata - Bangkok - {dest}", 42000, 3, "High"))
        options.append(opt("PU-004", "Unavailable Ship V007 via Port Blair", "V007", f"{origin} - Port Blair - Bangkok - {dest}", 72000, 4, "Medium"))
        options.append(opt("PU-005", "Over-budget fast air via Dhaka-Bangkok", air_v, f"{origin} - Dhaka - Bangkok - {dest}", int(budget + 60000), 1, "Low"))
        options.append(opt("PU-006", "Slow Van V012 delayed", "V012", f"{origin} - Chittagong - Kolkata - Yangon - {dest}", 50000, deadline + 4, "High"))
        options.append(opt("PU-007", "Budget flexible via Truck through Chittagong", pick_vehicle(weight, fallback="V013"), f"{origin} - Chittagong - Kolkata - Yangon - {dest}", feasible_cost(0.50, 10000, 50000), feasible_time(0.7), "Low"))

    elif "cargo damaged" in key:
        options.append(opt("CD-001", "Partial reroute after repacking via Kolkata", pick_vehicle(weight, fallback="V005"), f"{origin} - Chittagong - Kolkata - Yangon - Bangkok - {dest}", feasible_cost(0.60), feasible_time(1), "Medium"))
        options.append(opt("CD-002", "Replacement via Ship with insurance", ship_v, f"{origin} - Chittagong - Kolkata - Yangon - Kuala Lumpur - Singapore - {dest}", feasible_cost(0.58), feasible_time(0.8), "Low"))
        options.append(opt("CD-003", "Small Van insufficient for heavy cargo", "V006", f"{origin} - Khulna - Kolkata - Bangkok - {dest}", 36000, 3, "High"))
        options.append(opt("CD-004", "Unavailable heavy Truck with repair wait", "V003", f"{origin} - Dhaka - Bangkok - {dest}", 80000, deadline + 2, "High"))
        options.append(opt("CD-005", "Blocked route shortcut with damaged goods", "V001", f"{origin} - Kolkata - Bangkok - Kuala Lumpur - {dest}", 43000, 6, "High"))
        options.append(opt("CD-006", "Premium fast via Aircraft", air_v, f"{origin} - Dhaka - Singapore - {dest}", int(budget + 55000), 2, "Medium"))
        options.append(opt("CD-007", "Low-cost via Van through Yangon", pick_vehicle(weight, fallback="V016"), f"{origin} - Yangon - Bangkok - {dest}", feasible_cost(0.48, 9000, 45000), feasible_time(1.2), "Medium"))

    elif "major delay" in key:
        options.append(opt("MD-001", "Faster alternative via Kolkata-Yangon-Bangkok", pick_vehicle(weight, fallback="V008"), f"{origin} - Kolkata - Yangon - Bangkok - Kuala Lumpur - {dest}", feasible_cost(0.65), max(1, min(2, deadline-1)), "Low"))
        options.append(opt("MD-002", "Sea hybrid via Chittagong and Kuala Lumpur", pick_vehicle(weight, fallback="V016"), f"{origin} - Chittagong - Kolkata - Yangon - Bangkok - {dest}", feasible_cost(0.60), max(1, min(3, deadline-0.5)), "Medium"))
        options.append(opt("MD-003", "Small Van attempt via blocked Kolkata-Bangkok", "V006", f"{origin} - Dhaka - Kolkata - Bangkok - {dest}", 40000, 2, "High"))
        options.append(opt("MD-004", "Unavailable Ship supposed fast lane", "V007", f"{origin} - Port Blair - Bangkok - Singapore - {dest}", 75000, 2, "Medium"))
        options.append(opt("MD-005", "Blocked Kolkata-Bangkok direct", "V001", f"{origin} - Kolkata - Bangkok - {dest}", 39000, 1, "High"))
        options.append(opt("MD-006", "Over-budget premium Truck V011", "V011", f"{origin} - Dhaka - Bangkok - Kuala Lumpur - {dest}", int(budget + 70000), 1, "Low"))
        options.append(opt("MD-007", "Air rescue via Aircraft", pick_vehicle(weight, 'air', "V015"), f"{origin} - Dhaka - Singapore - {dest}", feasible_cost(0.85, 20000, 95000), 1, "Low"))

    else:
        v1 = pick_vehicle(weight, fallback="V001")
        options.append(opt("GEN-001", "Standard road via Kolkata Yangon", v1, f"{origin} - Chittagong - Kolkata - Yangon - Bangkok - {dest}", feasible_cost(0.60), feasible_time(1), "Low"))
        options.append(opt("GEN-002", "Sea route via Kuala Lumpur", ship_v, f"{origin} - Chittagong - Kolkata - Kuala Lumpur - Singapore - {dest}", feasible_cost(0.55), feasible_time(0.8), "Medium"))
        options.append(opt("GEN-003", "Small van via blocked Kolkata-Bangkok", "V006", f"{origin} - Kolkata - Bangkok - {dest}", 40000, 3, "High"))
        options.append(opt("GEN-004", "Unavailable vehicle via Dhaka Bangkok", "V003", f"{origin} - Dhaka - Bangkok - {dest}", 70000, 3, "Medium"))
        options.append(opt("GEN-005", "Blocked segment Kolkata-Bangkok", "V008", f"{origin} - Kolkata - Bangkok - {dest}", 42000, 4, "High"))
        options.append(opt("GEN-006", "Expensive fast via Bangkok Kuala Lumpur", "V011", f"{origin} - Bangkok - Kuala Lumpur - {dest}", int(budget + 50000), 1, "Low"))
        options.append(opt("GEN-007", "Air via Aircraft direct", pick_vehicle(weight, 'air', "V015"), f"{origin} - Singapore - {dest}", feasible_cost(0.70, 15000, 80000), 1, "Low"))

    if dest == "Jakarta":
        for o in options:
            if "Bangkok - Jakarta" in o["route_description"]:
                o["route_description"] = o["route_description"].replace("Bangkok - Jakarta", "Bangkok - Kuala Lumpur - Jakarta")

    for o in options:
        parts = [p.strip() for p in o["route_description"].split(" - ")]
        deduped = []
        for p in parts:
            if not deduped or deduped[-1].lower() != p.lower():
                deduped.append(p)
        o["route_description"] = " - ".join(deduped)

    return options
