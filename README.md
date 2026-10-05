# RouteWise 
Logistics Decision Support System
### AI-Based Recovery Decision Recommendation for Unexpected Shipment Problems

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/Flask-2.3-000000?style=for-the-badge&logo=flask" alt="Flask">
  <img src="https://img.shields.io/badge/Chart.js-FF6384?style=for-the-badge&logo=chartdotjs&logoColor=white" alt="Chart.js">
</p>

> **Description:** A logistics decision support system that finds the best action when a shipment faces unexpected problems. It compares routes and recovery options to minimize loss and maximize expected profit using A*, Dijkstra, CSP, and Hill Climbing.

---

## 📖 Project Overview

The RouteWise System is an AI-based project that helps logistics companies make better decisions when something unexpected happens during a shipment.
When a shipment runs into a problem such as a blocked route, an unavailable vehicle, or a damaged port , the system automatically analyzes the available recovery options and recommends the best one based on cost, delay, risk, and expected profit.

The system uses four algorithms working together:

1. **CSP** - Filters out options that are not possible
2. **Dijkstra** - finds the lowest-cost route
3. **Astar** - finds an efficient route toward the destination
4. **Hill Climbing** - improves the best available plan

The project uses a small simulated transportation network with predefined locations,routes, vehicles, costs, and travel times. 

---

## ❗ Problem Description

Unexpected incidents during transportation are common. When they happen, logistics teams must quickly evaluate multiple recovery options while considering cost, time, risk, and feasibility - all at the same time. Making this decision manually is difficult, slow, and often leads to poor choices.

RouteWise automates this decision loop in a transparent, reproducible way.

---

## 🎯 Project Objectives

- Generate possible recovery decisions for a disrupted shipment
- Remove decisions that violate important constraints (CSP)
- Find suitable alternative transportation routes (Dijkstra cheapest, A* fastest)
- Improve/compare candidate plans using an optimization decision rule (Hill Climbing 5% relative)
- Calculate cost, delay, risk and expected **Final Profit** for each plan
- Recommend the best available recovery decision with explainable rationale
- Compare the performance of the implemented algorithms (real measured metrics)

---

## 🚀 How to Setup and Run This Project

### Prerequisites
- Python **3.10+**
- `pip`

### 1. Clone
```bash
git clone <repository-url>
cd logistics-decision-support
```

### 2. Install
```bash
pip install -r requirements.txt
# requirements: Flask, (no pandas/ORM needed — CSV only)
```

### 3. Run
```bash
python app.py
```

### 4. Open
```
http://127.0.0.1:5000
# Flask binds 0.0.0.0:5000 → preview: https://5000-xxxx.e2b.app
```

**Flow to test:**
`Home → New Analysis → Shipment (10 locations, single Chittagong) → Incident → Processing → Result`

---

## 🔄 System Workflow

```
        SHIPMENT 
               │
               ▼
           INCIDENT 
               │
               ▼
              CSP 
               │    
               │
      ┌────────┴────────┐
      ▼                 ▼
 DIJKSTRA            A* Search
 Cost-based          Time-based
  route                route 
      │                 │
      └────────┬────────┘
               ▼
         CANDIDATE PLANS 
               │
               ▼
         HILL CLIMBING 
               │ 
               ├───────────────────┬───────────────────┐
               │                   │                   │
         Small (<5%)           Large (≥5%)           Tie (0%)
         Choose faster         Choose cheaper      Choose faster (A*)
               │                   │                   │
               └───────────┬───────┴───────────┬───────┘
                           ▼
                    FINAL DECISION
                           │
                           ▼
                    PROFIT RESULT (Financial Calculation)
```


## 🧠 Algorithms Used

**1. CSP (Constraint Satisfaction Problem)**
Checks 5 constraints: vehicle capacity ≥ cargo weight, arrival within deadline, vehicle available, route not blocked, recovery cost within budget. Violating options are removed.

**2. Dijkstra**
Finds the lowest-cost route. Weight = `cost_bdt`, uses priority queue on blocked=0 edges.

**3. A***
Finds the fastest route. Uses `f(n) = g(n) + h(n)` where `h` is Euclidean distance estimate. Different objective from Dijkstra (cost vs time).

**4. Hill Climbing**
Compares Dijkstra and A* routes using relative percentage:
`(|CostA-CostB| / min(CostA,CostB)) * 100%`
Threshold 5%: `<5%` → faster route, `≥5%` → cheaper route, tie → faster.

Algorithms run sequentially; each passes output to the next.

---


## 💰 Financial Calculation

**Formula (Revenue = Total Payment Received, user input):**
```
Final Profit = Revenue − Original Cost − Recovery Cost − Damage Cost − Delay Penalty
```
| Term | Description |
|------|-------------|
| **Revenue** | Total payment received for delivering the shipment (input, BDT) |
| **Original Cost** | Planned transportation cost before incident |
| **Recovery Cost** | Additional cost of chosen recovery (Hill-selected route) |
| **Damage Cost** | 2% of cargo value if incident = Cargo Damaged else 0 |
| **Delay Penalty** | 5,000 BDT per day late (`delivery_time > deadline`) |

---

## 📊 Evaluation Metrics

Four simple metrics measured with real `time.perf_counter()` values:

1.  **Execution Time** — Time taken by each algorithm (CSP, Dijkstra, A*, Hill) in ms.
2.  **Solution Quality** — Cost, time and risk of the selected plan.
3.  **Efficiency** — Nodes explored and how many options CSP filtered.
4.  **Convergence Behavior** — Hill Climbing result: percentage difference, classification (small/large), and which route was selected.

Shown with 4 Chart.js charts and a summary table.

---

## 🗂 Project File Structure

```
logistics-decision-support/
│
├── app.py                        # Flask entry, session flow, graph building (country + Road Blocked), financial & Hill wiring
│
├── algorithms/
│   ├── csp.py                    # CSP — 5 constraints, detailed log
│   ├── dijkstra.py               # Dijkstra — cheapest (cost)
│   ├── astar.py                  # A* — fastest (time, h= Euclidean*111/800)
│   └── hill_climbing.py          # Hill — 5% relative, small→faster / large→cheaper / tie→A*
│
├── modules/
│   ├── shipment.py               # Shipment validation (10 locations incl. Chittagong single, 1-200t integer, BDT commas, payment=Revenue)
│   ├── incident.py               # Recovery option generation per incident (incl. Aircraft, Road/sea/air grouping)
│   ├── financial.py              # Profit = Revenue - Original - Recovery - Damage(2%) - Delay(5k/d)
│   └── evaluation.py             # Aggregates 4 metrics for charts/tables
│
├── data/
│   ├── routes.csv                # 1,002 logical routes (from, to, distance_km, travel_time_hrs, cost_bdt, route_type, blocked) — road/sea/air ×1.15/1.35/1.0
│   ├── vehicles.csv              # 14 vehicles (Truck/Van/Ship/Aircraft, capacity, available, cost/km)
│   └── locations.csv             # 10 locations with country & lon/lat for A* heuristic
│
├── templates/
│   ├── index.html                # Home (hero, features)
│   ├── shipment.html             # Shipment form (dropdowns from locations.csv, integer tons, BDT commas, budget≤payment live hint)
│   ├── incident.html             # Incident cards (5 types incl. Aircraft card if needed)
│   ├── processing.html           # Sequential pipeline animation → /run_analysis
│   └── result.html               # 6 sections: Recommended, Why, Hill Breakdown (5%), Financial (Revenue=Payment), Evaluation 4-card, Charts, Options table
│
├── static/
│   ├── css/style.css             # Dark navy #0a0e1a + amber #f59e0b, Inter, 5-page responsive
│   └── js/main.js                # Form validation, budget≤payment warning, Chart.js rendering
│
├── requirements.txt
└── README.md
```

## 🛠 Technology Stack

- **Backend:** Python 3.10+, Flask
- **Frontend:** HTML + CSS + JS (vanilla, no Bootstrap/pandas)
- **Data:** CSV (`csv` module)
- **Charts:** Chart.js (CDN)
- **Style:** Inter font, dark navy `#0a0e1a`, amber `#f59e0b`

---

## 📎 Conclusion

RouteWise shows how **CSP, Dijkstra, A* and Hill Climbing** can cooperate on a practical logistics problem. CSP prunes infeasible options, Dijkstra (cheapest) and A* (fastest) offer contrasting candidates on a **logical, country-aware graph**, Hill Climbing decides via an explainable **5% relative** cost-time trade-off, and the financial module judges the result on **profit**. Kept as a small simulation, the project stays focused on algorithms while remaining runnable, testable and demonstrable end-to-end.

---

## 📝 License

## Team - Lemon Tea



