# Reactor lab: scope, verification and owner-run checks

The browser uses Three.js, with the source-based **inverted YSZ/Pt hollow-anode** arrangement from Yu et al. Figure 1(b), sections 2.2.1–2.2.2. The Mo cathode is central, regolith is inside the YSZ tube, Pt collector is outside it, and alumina supplies secondary containment. Meshes are normalized schematic shapes, not dimensionally recovered CAD. The lower heated region is illustrated; gas dots show a path, not measured bubble dynamics or production rate.

Primary geometry source: https://ntrs.nasa.gov/citations/20250004626
NASA thermal study: https://tfaws.nasa.gov/wp-content/uploads/TFAWS2024-ID-04.pdf
The latter concerns a different reactor/thermal-vacuum model and is not reproduced by this solver. Its public illustrations omit proprietary detail. Do not interpret reference images of microwave water extraction or FFC molten-salt cells as this MRE configuration.

## What is calculated

`reactor_field.py` solves steady radial heat conduction in a constant-property annulus with ohmic bulk heating and fixed inner/outer temperatures. The annulus is an idealized **bulk melt scenario**, not a model of the complete YSZ/Pt electrochemical cell. In x = ln(r/a), the heat equation is a constant-source second derivative, solved by a 48/96-cell finite-volume discretization. Bulk potential/current use the exact coaxial conduction solution. J = I/(2πrh), R = ln(b/a)/(2πhσ), q = J²/σ. End heat loss, radiation, convection, melting, interface resistance, electrolysis kinetics and chemistry are excluded.

The independent closed-form temperature is T(x) = Ti + (To−Ti)x/L + [I/(2πh)]² x(L−x)/(2σk), L=ln(b/a). The report gives its error, mesh-refinement change and heat-balance residual. These are numerical verification, not physical validation. Boundary/property values loaded by the demo button are explicit assumptions, not NASA values or recommended setpoints. Temperature/current colors display the computed radial profile extruded in height/azimuth; no unsupported 3-D hotspots are created.

## Workflow

1. Enter the measured experiment record as usual.
2. Open **Review & assess → Reactor lab → Calculate and compare a scenario**.
3. Optionally load labelled demo assumptions, edit values and click **Calculate scenario**. This local numerical action uses no Meta request.
4. Change current or other assumptions and click **Compare changed scenario** to compare computed power/temperature. The last solved scenario is attached to the next assessment; merely editing an unsolved scenario does not change that receipt.
5. Authorize **Assess with Meta** yourself. Meta may select `reactor_field_simulation` as its critic tool; it is not forced to select it. A selected tool result is saved in the immutable assessment and supplied to critic/final review.
6. In the saved result, use component selection and investigation-stage buttons. Orange follows the selected review's concern status; it does not mean a measured failure location or probability. Wall-loss overlay marks the component, not predicted local damage. No degradation law is supplied or claimed.
7. Read plain-language evidence and download full JSON separately. Old reports remain unchanged and can retain old model mistakes.

## Targeted recheck

From the repository, owner runs:

```sh
PYTHONPATH="$PWD/src" python -m unittest discover -s tests -v
cd frontend
npm install
npm run build
npm test
```

Restart the Python backend using the same command/port (8769) used before; restart Vite (`npm run dev`) and refresh once. No automatic Meta rerun occurs.

Checks to inspect: zero current/equal boundary temperatures is isothermal; doubling scenario current multiplies bulk Joule power by four; analytic error decreases on refinement; energy residual is small; missing/invalid geometry is rejected; changed scenario produces a different receipt.

For a new authorized Meta run, explicitly inspect whether independent generation approximately equal to collection is correctly described as evidence **against** major collection loss; generation greater than collection supports uncollected oxygen only with matched validated accounting. Check that synthetic run records are not confused with the real published research sources. Prompt/reference fixes do not establish that every future model response will be correct.

## Optional Meta-generated assets

Meta SAM 3D Objects can reconstruct visual meshes from an image and mask: https://github.com/facebookresearch/sam-3d-objects . Official Meta Model API SAM 3.1 documentation currently describes segmentation, not a verified SAM-3D mesh endpoint: https://dev.meta.ai/docs/sam/overview . No fictional endpoint or extra paid call is added here. Reconstructed meshes would need scale/component review before use as visual assets; inferred hidden geometry is not verified engineering geometry. No external asset-generation service is required for this implementation.
