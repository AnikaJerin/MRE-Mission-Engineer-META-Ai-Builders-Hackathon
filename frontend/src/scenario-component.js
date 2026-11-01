export function scenarioComponent(current, scene) {
 if(current?.material_forecast?.component)return current.material_forecast.component;
 if(current?.model==='collection_accounting')return 'gas';
 const components=scene?.result?.hypotheses?.[current?.hypothesis_number-1]?.components||[];
 if(current?.model==='current_allocation')return components.find(c=>['melt','anode','cathode','wall'].includes(c))||'melt';
 return components[0]||'melt';
}
