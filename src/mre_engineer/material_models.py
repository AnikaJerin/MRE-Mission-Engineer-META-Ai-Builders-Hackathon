"""Explicit, user-parameterised material scenarios; separate from AI reviews."""
import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4
from .evidence import EvidenceError
from . import reactor_degradation as models
from .reactor_calibration import ysz_conductivity, mo_resistivity

FUNCTIONS = {
    'linear': models.linear_degradation,
    'parabolic': models.parabolic_degradation,
    'arrhenius': models.arrhenius_rate,
    'thermal_cycles': models.coffin_manson_cycles,
    'thermal_stress': models.thermal_stress,
    'lifetime': models.lifetime_prediction,
}

def calculate(data):
    if not isinstance(data, dict) or set(data) != {'model', 'parameters'}:
        raise EvidenceError('Supply a model and its parameters')
    name, parameters = data['model'], data['parameters']
    if not isinstance(name, str) or name not in FUNCTIONS or not isinstance(parameters, dict):
        raise EvidenceError('Unknown material model or invalid parameters')
    try:
        result = FUNCTIONS[name](**parameters)
        if name == 'arrhenius':
            result = {'rate': result, 'units': 'Same rate units as supplied pre-exponential A'}
        json.dumps(result, allow_nan=False)
    except (TypeError, ValueError, OverflowError, ZeroDivisionError) as exc:
        if isinstance(exc, EvidenceError):
            raise
        raise EvidenceError('Check all required model parameters and their numerical range') from exc
    return {'model': name, 'parameters': parameters, 'result': result,
            'scope': 'Conditional model scenario, not a calibrated failure forecast. Percentage bands are sensitivity bounds, not statistical confidence intervals.',
            'api_calls': 0}

def save(root, data):
    if not isinstance(data, dict) or set(data) != {'assessment_id', 'scenario'}:
        raise EvidenceError('Assessment and scenario are required')
    from .reactor_hypotheses import assessment
    from .investigation import digest
    assessment(root, data['assessment_id'])
    value = calculate(data['scenario'])
    value.update(id=uuid4().hex, assessment_id=data['assessment_id'], created_at=datetime.now(timezone.utc).isoformat())
    value['sha256'] = digest(value)
    directory = Path(root)/'outputs'/'material-models'/value['id']
    directory.mkdir(parents=True, exist_ok=False)
    (directory/'report.json').write_text(json.dumps(value, indent=2, allow_nan=False))
    return value

def properties(data):
    if not isinstance(data, dict) or set(data) != {'temperature_C'}:
        raise EvidenceError('Supply temperature_C')
    temperature = models._check_positive_finite(data['temperature_C'], 'temperature_C')
    return {'temperature_C': temperature, 'ysz_conductivity_S_m': ysz_conductivity(temperature),
            'mo_resistivity_ohm_m': mo_resistivity(temperature),
            'scope': 'Illustrative material coefficients; NOT fitted to this cell. Solid YSZ conductivity is not molten-regolith conductivity.', 'api_calls': 0}

def latest(root, assessment_id):
    from .reactor_hypotheses import assessment
    from .investigation import digest
    assessment(root, assessment_id)
    rows=[]
    for path in (Path(root)/'outputs'/'material-models').glob('*/report.json'):
        value=json.loads(path.read_text())
        if value.get('assessment_id')==assessment_id:
            if value.get('sha256')!=digest({k:v for k,v in value.items() if k!='sha256'}):
                raise EvidenceError('Saved material scenario changed')
            rows.append(value)
    return {'latest':max(rows,key=lambda v:v['created_at']) if rows else None}
