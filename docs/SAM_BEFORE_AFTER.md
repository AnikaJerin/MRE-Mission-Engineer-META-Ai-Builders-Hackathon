# Before/after component evidence

This additive feature retains previous assessments and runs its own reviewer and critic. No sample results are embedded. Use two photographs of the same physical component with a ruler/calibration target in the object plane, a fixed camera direction, and a comparable unobscured view. Two unrelated publication photos are not before/after ground truth.

## Owner test flow

1. Restart the Python backend after installation. Keep the frontend running. Open a completed saved assessment → Hypotheses & 3D → Before & after.
2. Select component and short visible-object prompt. Enable the single-upload SAM consent. Upload **before** PNG. Wait for completion. Repeat consent and upload **after** PNG. Each upload makes one explicit SAM request. Existing saved SAM captures can also be selected.
3. Select the correct mask in each preview. Small masks of wires or fittings must not be selected as the electrode silhouette. Masks touching image edges are rejected for comparison.
4. Enter measured mm/pixel for each original uploaded image: known target length in mm divided by its length in pixels. Enter absolute scale bounds. These must come from calibration; zero is an explicit exact-scale assumption. No universal scale can be supplied for an arbitrary photograph.
5. Confirm the same physical component, mask quality, and comparable view. Camera registration is owner-confirmed, not automated. Describe occlusion, lighting and calibration records.
6. Enable two-request Wonder consent → Compare images & review evidence. The backend decodes saved SAM events itself using Meta's installed parser, computes projected metrics and sends those alongside immutable assessment measurements and applicable source comparisons to a separate reviewer, then critic. A failed request retains partial results and is never silently retried.
7. Read area/width changes and sensitivity bands. Review/critic comments cite evidence IDs. Use Inspect comparison in 3D to select the mapped existing component and show its two photographs, measured projected change and uncertainty. This never deforms geometry to imply inferred corrosion depth.
8. Download the persisted report. Reopening does not repeat paid requests. UI selections/scales are stored as a browser draft; reports and source images are saved on disk.

## Calculations and limits

For each selected mask, map its decoded raster and bounding box back to the original uploaded image grid. Count foreground pixels and horizontal silhouette widths. Projected area = pixels × (mm/pixel)². Width = pixels × mm/pixel. Area percentage change = 100 × (after/before − 1). Compare physical units even if input scales differ.

Area sensitivity combines a one-pixel four-neighbour erosion/dilation with the supplied scale bounds. Change interval = after-low − before-high through after-high − before-low. It is not a statistical confidence interval and does not capture all camera, illumination, occlusion or SAM errors. Width values are orientation-dependent point estimates, not depth estimates. No mass loss, 3D surface area or confirmed degradation diagnosis is inferred.

The server requires Node and installed frontend @meta-sam/parser. If node is not on PATH, set MRE_NODE_BINARY to the Node executable before starting the backend. No CUDA or local GPU is used for cloud segmentation.

## Verification

Tests are authored in tests/test_sam_comparison.py. Owner runs the full test suite and frontend build, then the live flow. Passing unit tests does not certify SAM accuracy or scientific diagnosis. Validate segmentation and quantitative change against independently measured before/after samples before making accuracy claims.
