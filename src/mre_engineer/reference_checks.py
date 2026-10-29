"""Independent numeric references: Decimal/Fraction, no production-physics import."""
from decimal import Decimal, localcontext
from fractions import Fraction


def numeric_references(case):
    o=case["observations"]
    if case["id"]=="hollow-anode-review":
        with localcontext() as context:
            context.prec=50
            faraday=Decimal("6.02214076e23")*Decimal("1.602176634e-19")
            charge=Decimal(str(o["current_A"]))*Decimal(str(o["electrolysis_h"]))*Decimal(3600)
            mass=charge*Decimal("31.998")/(Decimal(4)*faraday)
        initial=Fraction(str(o["initial_resistance_ohm"]));final=Fraction(str(o["final_resistance_ohm"]))
        return {"ideal_o2_g":float(mass),"resistance_change_percent":float((final/initial-1)*100)}
    if case["id"]=="lr1-core-review":
        earlier=Fraction(str(o["poster_rate_kg_h"]));later=Fraction(str(o["abstract_rate_kg_h"]))
        return {"reported_rate_difference_kg_h":float(earlier-later),"reported_rate_ratio_percent":float(later/earlier*100)}
    raise ValueError("No independently reviewed reference for this case")
