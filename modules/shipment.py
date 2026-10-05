VALID_LOCATIONS = ["Dhaka", "Khulna", "Kolkata", "Chittagong", "Yangon", "Bangkok", "Port Blair", "Kuala Lumpur", "Singapore", "Jakarta"]
VALID_TRANSPORT = ["Truck", "Van", "Ship", "Aircraft"]

def _parse_number(val, field_name="value"):
    if val is None:
        raise ValueError(f"{field_name} is required")
    s = str(val).strip().replace(",", "").replace(" ", "").replace("BDT", "").replace("bdt", "").strip()
    if s == "":
        raise ValueError(f"{field_name} must be a number")
    try:
        return float(s)
    except:
        raise ValueError(f"{field_name} must be a number, got '{val}'")

class Shipment:
    def __init__(self, origin, destination, cargo_weight_tons, cargo_value_bdt, original_cost_bdt,
                 delivery_deadline_days, transportation_type, recovery_budget_bdt, total_payment_received_bdt=None):
        if origin not in VALID_LOCATIONS:
            raise ValueError(f"Origin must be one of {VALID_LOCATIONS}, got {origin}")
        self.origin = origin

        if destination not in VALID_LOCATIONS:
            raise ValueError(f"Destination must be one of {VALID_LOCATIONS}, got {destination}")
        if destination == origin:
            raise ValueError("Destination must be different from origin")
        self.destination = destination

        cw = _parse_number(cargo_weight_tons, "Cargo weight")
        if cw <= 0 or cw > 500:
            raise ValueError("Cargo weight must be between 0 and 500 tons")
        self.cargo_weight_tons = cw

        cv = _parse_number(cargo_value_bdt, "Cargo value")
        if cv < 1000:
            raise ValueError("Cargo value must be at least 1,000 BDT")
        self.cargo_value_bdt = cv

        oc = _parse_number(original_cost_bdt, "Original cost")
        if oc < 1000:
            raise ValueError("Original cost must be at least 1,000 BDT")
        self.original_cost_bdt = oc

        dd = int(_parse_number(delivery_deadline_days, "Delivery deadline"))
        if dd <= 0 or dd > 365:
            raise ValueError("Delivery deadline must be 1-365 days")
        self.delivery_deadline_days = dd

        if transportation_type not in VALID_TRANSPORT:
            raise ValueError(f"Transportation type must be one of {VALID_TRANSPORT}")
        self.transportation_type = transportation_type

        rb = _parse_number(recovery_budget_bdt, "Recovery budget")
        if rb < 5000:
            raise ValueError("Recovery budget must be at least 5,000 BDT")
        self.recovery_budget_bdt = rb

        if total_payment_received_bdt is None or str(total_payment_received_bdt).strip() == "":
            self.total_payment_received_bdt = float(cv * 1.25)
        else:
            tp = _parse_number(total_payment_received_bdt, "Total Payment Received")
            if tp < 1000:
                raise ValueError("Total Payment Received must be at least 1,000 BDT")
            self.total_payment_received_bdt = tp

    def to_dict(self):
        return {
            "origin": self.origin,
            "destination": self.destination,
            "cargo_weight_tons": self.cargo_weight_tons,
            "cargo_value_bdt": self.cargo_value_bdt,
            "original_cost_bdt": self.original_cost_bdt,
            "delivery_deadline_days": self.delivery_deadline_days,
            "transportation_type": self.transportation_type,
            "recovery_budget_bdt": self.recovery_budget_bdt,
            "total_payment_received_bdt": self.total_payment_received_bdt,
            "total_payment_bdt": self.total_payment_received_bdt,
            "revenue_bdt": self.total_payment_received_bdt
        }

    def __repr__(self):
        return f"Shipment({self.origin}->{self.destination}, {self.cargo_weight_tons}t)"

def validate_shipment_data(data):
    return Shipment(
        origin=data.get('origin'),
        destination=data.get('destination'),
        cargo_weight_tons=data.get('cargo_weight_tons'),
        cargo_value_bdt=data.get('cargo_value_bdt'),
        original_cost_bdt=data.get('original_cost_bdt'),
        delivery_deadline_days=data.get('delivery_deadline_days'),
        transportation_type=data.get('transportation_type'),
        recovery_budget_bdt=data.get('recovery_budget_bdt'),
        total_payment_received_bdt=data.get('total_payment_received_bdt') or data.get('total_payment_bdt') or data.get('revenue_bdt')
    )
