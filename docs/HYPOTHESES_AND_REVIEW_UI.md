# Result-linked hypothesis layer and organized review UI

## Preserved workflow

The existing five-request assessment, first review, critic, final review and exports are unchanged. No historical assessment or hypothesis file is overwritten. Follow investigation and saved results appear only under **Review & assess**. Opening the application restores the input draft, without automatically opening a historical assessment. Use **Saved reviews** explicitly to open one.

Result sections: Summary; Measurements; Review & critic; Evidence; Hypotheses & 3D; Researcher review. The existing structured review is still available in its own section.

## New, explicitly authorized action

After a completed assessment, open **Hypotheses & 3D**. A neutral schematic appears until a hypothesis set is generated. Authorize the separate single Meta request and click **Create result-linked hypotheses with Meta**. The model receives this immutable assessment's inputs, calculated metrics, published applicability comparisons, final review and critic. It returns 2–3 competing, unconfirmed hypotheses with named components and exact evidence references. The backend checks the schema, component IDs, field/metric availability and source/tool references. These checks do not certify every narrative inference.

Selecting a 3D component shows the model hypothesis, cited measurements, calculated values/formulas, research references, applicability and proposed distinguishing observation. Orange means **component to investigate**, never diagnosed failure or inferred damage percentage. Mesh dimensions are not generated from a hypothesis; the selected source-based arrangement remains fixed.

For changed results, open the new completed assessment, choose an earlier hypothesis set in the optional selector, and click **Reconsider hypotheses with this result**. The model must reconsider every prior hypothesis once: retained, revised or rejected, with reasons grounded in current evidence. The earlier set is context, not ground truth. No forced change is imposed. The new version links both the previous set and the new assessment hash.

Versions and actual model submission records are stored separately in `outputs/reactor-hypotheses/<id>/`. GET/refresh reads saved versions and never starts paid work. A failed generation preserves the original review and any prior successful version. The existing local budget ledger is used; one request reserves $0.25 locally, not a provider-enforced charge ceiling.

## SAM boundary

SAM 3D reconstructs a visual asset from an image/mask; it does not produce engineering hypotheses. Hypotheses here come from the Meta reasoning API. Official setup requires Linux and NVIDIA GPU >=32 GB VRAM: https://github.com/facebookresearch/sam-3d-objects/blob/main/doc/setup.md . No unsupported hosted SAM-3D endpoint, GPU installation or automatic generation is claimed.

**Optional SAM 3D / Blender visual mesh** accepts a completed embedded GLB (<=20 MB) in the browser. Name component meshes during reconstruction/editing, then map their names to vessel, YSZ wall, anode, cathode, melt or gas outlet. The agent's named components can highlight those mapped meshes. This is user-declared visual mapping, not validated geometry. The asset stays in the current browser session; assessment/hypothesis evidence is separately persisted. External asset resources are rejected; export one embedded GLB. Thermal/current fields use only the explicitly defined numerical scenario geometry, never an inferred SAM surface.

Default source arrangement: Yu et al. 2025 Figure 1(b), https://ntrs.nasa.gov/citations/20250004626 . Different/unknown reactor configurations remain visibly flagged; that geometry is not inferred from supplied values.

## Owner-run validation

No tests, server, GPU inference or paid request were run by the assistant.

```sh
PYTHONPATH="$PWD/src" python -m unittest discover -s tests -v
cd frontend
npm test
npm run build
```

Restart the existing backend on port 8769 and Vite on 5173. No new npm dependency is required beyond the previously added Three.js.

Manual checks:

1. New experiment / Measurements / Reference data: no Follow investigation or saved review below them.
2. Saved reviews → open a completed result → Review & assess: switch all result tabs; verify original review and critic text remain identical.
3. Hypotheses & 3D: before generating, no model hypothesis/highlight is fabricated. Check explicit extra-request consent.
4. Owner generates one set: verify actual request count, timestamp, cited metrics and sources on selected components.
5. New result + previous set: verify retained/revised/rejected explanations and a new version ID; prior review/version bytes remain unchanged.
6. Reload saved hypothesis view: ledger request count does not increase.
