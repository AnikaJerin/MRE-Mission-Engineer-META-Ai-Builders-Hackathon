"""Independent T12 arithmetic. Does not import the production physics module."""
from decimal import Decimal, localcontext
from fractions import Fraction


def calculate(task):
    if task is None:return None
    if task['kind']=='charge':
        with localcontext() as ctx:
            ctx.prec=50
            faraday=Decimal('6.02214076e23')*Decimal('1.602176634e-19')
            return float(Decimal(str(task['current_A']))*Decimal(str(task['duration_h']))*Decimal(3600)*Decimal('31.998')/(4*faraday))
    if task['kind']=='annual_rate':return float(Fraction(str(task['annual_kg']))/Fraction(str(task['hours_per_year'])))
    raise ValueError('Unreviewed numeric task')
