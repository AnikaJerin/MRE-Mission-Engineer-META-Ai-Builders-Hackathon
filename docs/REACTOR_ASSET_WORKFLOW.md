# Reactor asset and diagnostic workflow

Previous assessments, T12 freezes, research registry, drafts and budget history are not overwritten.
Wonder remains the reasoning model. SAM 3.1 is a separate reference-image segmentation request.

## Owner setup — do not skip dependency installation
From the repository root:

```sh
python -m pip install --no-deps -e .
python -m unittest discover -s tests -v
cd frontend
npm install
npm run build
npm run dev
```

Keep Vite running. In a second terminal at repository root, export MODEL_API_KEY as before and start the backend with your existing `python -m mre_engineer serve` command/port configuration. Restart the old backend once so it loads the new routes. No assessment or SAM call occurs on page load.

## 1. Source image → SAM (explicit cloud call)
Reference design: https://ntrs.nasa.gov/citations/20250004626 — Figure 1(b), methods 2.2.1–2.2.2, supplementary Figure S1.
Select/crop a visible source photograph or diagram to PNG, 16–1200 pixels per side and <=750 KB. Verify permission before sharing a publication image; NASA hosting alone does not establish copyright permission. Do not substitute FFC molten-salt, microwave water extraction, or another reactor design.
In Review & assess → Hypotheses & 3D → Reference assets:
- Upload the reference PNG, select the component, enter one concrete visible-object phrase (for example `ceramic tube`).
- Enter the publication URL, exact figure/page, and your permission/licence note.
- Tick sharing consent and click Segment reference with SAM.
- Expect a saved real SAM mask overlay or an explicit no-match result. Never a fabricated mask.
- Request/image provenance persists in outputs/sam-segmentations. Opening saved results is read-only.

The mask guides visible-part modelling; it does not determine hidden surfaces, dimensions or damage. SAM does not diagnose the reactor and does not create hypotheses. The local renderer needs WebGL only; cloud SAM needs no local GPU. SAM 3D Objects has not been represented as a hosted API here.

## 2. Blender → GLB
Run once from repository root (requires installed Blender):

```sh
/Applications/Blender.app/Contents/MacOS/Blender --background --python scripts/build_reactor_asset.py -- --output outputs/reactor-assets/yu2025-v1
```

This builds a normalized source-based approximation with central Mo cathode, alumina sheath, YSZ containment, exterior Pt collector, outer alumina enclosure, endplate and gas connections. Visual dimensions are explicit assumptions, not published CAD. The exporter does not claim that these meshes were reconstructed by SAM. Inspect/refine against your source image/mask in Blender if needed.

In Hypotheses & 3D → Source-based Blender visual mesh, choose the exported reactor.glb. Canonical part names map automatically to evidence-linked components. Orbit, zoom and select components. A GLB import remains local to this browser session; the source image/mask and assessment reports persist separately. Do not infer solver geometry from the imported mesh.

## 3. Numerical scenario
The existing Reactor Lab accepts eight explicit geometry/property/boundary values. It solves steady radial annular conduction with bulk ohmic heating and checks an analytic solution, heat balance and refinement. The displayed field is extruded in 3D, not a full 3D CFD solution. No kinetics, YSZ interface, convection, radiation, phase change or lifetime prediction is asserted. Changing inputs and calculating a new scenario produces new numbers; it does not change previous saved reviews.

## 4. Assessment → revisable hypotheses → component highlight
Enter actual or clearly labelled synthetic measurements. Assess with Wonder, inspect First review → Critic → Final review. Then explicitly generate the additive hypothesis layer. Reconsider a previous set against a new completed assessment to obtain retained/revised/rejected hypotheses with evidence. Component clicks show measurements, calculations, applicability and distinguishing evidence requests. Hypotheses never rewrite the original review or fabricate mesh dimensions.

## 5. Known-construction diagnostic evaluation
Run from repository root, in one terminal only:

```sh
PYTHONPATH="$PWD/src" python -m mre_engineer.reactor_diagnostics freeze --name diagnostics-v1
PYTHONPATH="$PWD/src" python -m mre_engineer.reactor_diagnostics run --name diagnostics-v1 --freeze-name diagnostics-v1 --allow-api-call
```

At most 15 Wonder requests, $3.75 local reservation envelope (not provider cap). Cases compare matched oxygen balance, material observations and unresolved calibration/window evidence. The model sees observations, not construction labels. One-pass, critic/revision and equal-call resampling are saved against a deterministic checklist. Failures/coverage remain visible; no automatic retries. Use a new name rather than overwriting a freeze/run.

Open Hypotheses & 3D → Known-cause synthetic diagnostic evaluation → Refresh saved evaluation. It displays the saved model comments and reference comparison without new calls. These three transparent development scenarios are not a held-out real-reactor benchmark, NASA fault truth or evidence of general engineering superiority. Existing T12 remains separately versioned.

## Test status
Code and regression tests are authored. The assistant has not run tests, Blender, build, simulations or paid calls, per owner instruction. Complete the commands above before describing this extension as tested.
