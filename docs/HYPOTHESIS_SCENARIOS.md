# Forward scenarios and reconstruction

Existing reviewer, critic and final assessment are unchanged. All new work is under Hypotheses & 3D.

## Owner test (no tests or APIs were run by the implementer)
1. Restart backend on port 8769; keep frontend on 5173. Open an existing completed assessment and its saved hypotheses.
2. Under Test the hypotheses, load editable demo assumptions. These are synthetic assumptions, not NASA operating limits. Check the pre-submit summary: duration 3600 s, allocation 0.8, recovery 0.8, resistance multiplier 1.103896.
3. Read each hypothesis. Map collection loss to collection accounting; current diversion to current allocation; electrical change to equivalent resistance. These explicit mappings are sensitivity-test requests; the agent still ranks the evidence.
4. For an optional material forecast, choose the actual component (wall for the current synthetic wall record), loss 40 µm, bound 5 µm, exposure 3 h, additional time 3 h, initial thickness 1000 µm, source SYNTHETIC scenario, identical future conditions checked. Do not relabel wall measurements as electrode measurements.
5. Consent to two Wonder calls and click Rank, simulate & recommend. Open Simulation; select Baseline, H1, H2, H3. The existing 3D viewer is reused.
6. H1/H2 demo collected predictions both approximately 0.07163335 g: ambiguity must remain. H2 generated oxygen changes; H1 generation stays fixed. No fabricated spatial gas-loss field is rendered.
7. H3 bulk voltage and Joule power increase about 10.39%. Current density is unchanged at fixed current/geometry. A local temperature difference may be tiny; peak stays 1600 °C because that boundary is imposed. Do not expect a dramatic invented hotspot.
8. Conditional recession at constant rate: 13.3333 µm/h, total loss 80 µm (70–90 bound), remaining thickness 920 µm after another 3 h. This is not experimentally validated corrosion prediction or crack growth.
9. Recommendation uses actual computed receipts. Validation reports numerical verification separately from owner-declared experimental references. Do not use the same assumed input as an independent measured validation target.

Run locally:
```sh
PYTHONPATH="$PWD/src" python -m unittest discover -s tests -v
```
The full suite is owner-run. Prior immutable failed records remain failed.

## Model definition
Radial annulus: R=ln(b/a)/(2πhσ), J(r)=I/(2πhr), P=I²R. Steady radial conduction solves constant-property heat balance with fixed inner/outer temperatures and insulated ends. Interfaces, electrochemical kinetics, convection, radiation, phase change and crack growth are excluded. 1600/1500 °C are explicit boundary assumptions, not a conversion of a single sensor into measured spatial data. Finite-volume samples lie inside the boundaries; their colours can therefore span 1500.5–1599.5 °C while peak including boundary is 1600 °C.

Reference arrangement: [Yu 2025](https://ntrs.nasa.gov/citations/20250004626). This source does not validate the demo geometry/properties or a universal corrosion law. [NASA 2024 thermal work](https://tfaws.nasa.gov/wp-content/uploads/TFAWS2024-ID-04.pdf) concerns a different multiphysics model; this solver does not reproduce it.

## Actual SAM 3D path
SAM 3.1 cloud generates masks, not 3D meshes. First use the existing Reference assets / SAM tab with an actual source photograph, then inspect the saved mask.

```sh
node scripts/export_sam3d_input.mjs SAVED_SAM_ID
```
This exports the largest actual mask only when full-image alignment is established. Empty/cropped masks stop explicitly. No API is called by export.

On an external environment meeting the [official SAM 3D Objects requirements](https://github.com/facebookresearch/sam-3d-objects/blob/main/doc/setup.md), with approved model weights:
```sh
python scripts/reconstruct_sam3d.py --sam3d-repo /path/sam-3d-objects --pipeline /path/checkpoints/pipeline.yaml --bundle /path/sam3d-inputs/SAVED_SAM_ID --output /path/new-reconstruction
```
Then on the Mac:
```sh
/Applications/Blender.app/Contents/MacOS/Blender --background --python scripts/refine_sam3d_asset.py -- /path/new-reconstruction/component.glb /path/refined/component.glb wall
```
Import the GLB under Source-based Blender visual mesh in the existing viewer; canonical names map to components. A reconstructed single component is not a complete assembled reactor. Thermal/current overlays remain on the documented idealized solver geometry; visual meshes are not automatically verified computational meshes. Reconstruction, Blender refinement and cloud segmentation have NOT been run by the implementer. An actual mesh is pending an owner SAM run and supported external SAM 3D runtime. No unverified cloud SAM 3D endpoint is claimed.
