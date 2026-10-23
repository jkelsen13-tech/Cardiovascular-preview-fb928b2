# Outflow pathways repair

This changes only the heart Outflow presentation. The Section and four-chamber views, original source topology, numerical model, contextual/floating audio, recordings, and transcripts are retained. This is illustrative teaching geometry, not patient anatomy, segmented blood lumens, or computational fluid dynamics.

## Observed defect

The old Outflow view hid atrial and venous source structures but retained their center-to-center circulation arrows. Those arrows also ignored ordinary tissue depth. The aortic/pulmonary arrows used chamber, valve, and vessel bounding landmarks rather than source lumen contours. Section and Outflow therefore submitted identical legacy routes even though their visible anatomy differed. The continuous four-chamber occupancy display was not used by either view. The shared numerical valve gates and signed flow were correct and have not been replaced.

## Scoped correction

Outflow now shows two continuous proximal paths: LV → aortic valve → ascending aorta and RV → pulmonary valve → pulmonary trunk. Source ventricles, septum, and vessels remain in their original registration; transparent walls reveal both paths. An Outflow-only oblique preset separates their valve roots. The original Section crop/rendering is retained.

Each upstream endpoint is a conservative chamber-space witness from the existing source section mask, with septal tissue excluded. The connecting centerline reaches the actual source valve-frame center without crossing its own chamber wall or the septum. Its wall clearance constrains the fluid radius and surrounding illustrative tract wall. The ventricular/root connector is **inferred**, not a source-segmented outflow tract. Downstream center samples come from closed nested inner contours of the original ascending aorta or pulmonary trunk; the display stops before unresolved/open branch geometry. It does not claim to show flow through the complete arch or pulmonary arterial tree.

The final tube is piecewise linear, avoiding spline overshoot. Fluid and direction cones use the original sample's valve/pressure/Q gate and integrated flow displacement. There is no added animation clock. Ordinary depth testing remains enabled. The full roots are retained in the transparent Outflow view rather than being removed by the Section halfspace. No geometry is moved into the foreground to evade occlusion.

Explicit valve opening/attachment inspections retain their local aperture-bounded representation. An isolated arterial trace renders only the source-fitted downstream arterial portion, starting at the first qualified closed contour. Its Q/travel uses the existing systemic or pulmonary-bed edge; arterial reservoir flow may continue with a closed semilunar valve. Its inferred ventricular connector stays hidden. The numeric trace panel and existing bed schematic retain their original physiology. Hidden-host/extracardiac legacy arrows are not restored in Outflow.

## Source provenance and UI cost

`heart-study-v3/assets/source-geometry.js` SHA-256:
`5f3f615dce33e883f327630724009ba424f90866aa4b00dc30023007bf76315c`.

The baked `registeredOutflowRoutes` in `sourced-anatomy.js` contains the exact fit data. Normal UI entry does not perform source-triangle fitting. The exported `outflowRoutes` fitter is used only by the offline verification; the test recomputes it and compares every baked point, radius, clearance, and source slice against the unchanged source. The initial exploratory runtime fit took approximately 17 seconds in Node VM and was removed from the UI path.

## Verification

From the repository root, with the existing installed dependencies:

```sh
OUTFLOW_CPU_OUT=/tmp/outflow-cpu node tools/heart-v3/outflow-repair-cpu.cjs
node tools/contextual-audio/verify.cjs
CARDIO_BASE_URL=http://127.0.0.1:8883/ OUTFLOW_BROWSER_OUT=/tmp/outflow-browser python tools/heart-v3/outflow-repair-browser.py
```

The browser test uses installed `/usr/bin/chromium` with its sandbox enabled and excludes unsafe SwiftShader/self-XSS defaults. It observes the renderer getter through a small wrapper, checks that fetched source bytes match the local tested files, exercises native phase/rotation/inspection/trace controls, captures desktop/tablet/phone views, and checks independent user-initiated narration through browser media events. Screenshots and media events do not establish physical display or speaker timing.

CPU preservation uses private source commit `c6067253eb84c01a9ce8bb77563f8eb10463cbe3` by default. In the public preview history, use runtime-equivalent baseline `OUTFLOW_BASELINE=e7912e68dc39f5e88dd4715ae51a97b820f24c25`. The override selects comparison history; it does not change geometry acceptance criteria. The test preserves every original diagnostic key for 105 non-Outflow states at 55/75/110 BPM, checks 288 full-cycle Outflow samples and 576 valve gates, source topology, direct inspections and isolated trace behavior. Final deformed core/collar rings are checked against source wall/septum distance bounds at densely interpolated positions across five phases, including the valve-to-artery transition. Moving cone envelopes are checked at all active positions in a 96-sample cycle, with expected coverage derived from the authoritative model.

Historical guards are unchanged. The historical sourced-visibility guard pins `1c60012a8113c931dc2196258646fdd439bd2be0`, whose required vendor path is absent in this recovery history; its raw missing-path failure is retained privately. Some old assertions also explicitly preserved unoccluded legacy Outflow paths and are superseded by the owner's corrected requirement. They have not been rewritten to claim a pass.

## Limits

Source-fit clearance and rendered screenshots establish bounded registration/presentation checks, not anatomical validation of the inferred tract. Radius/thickness are display units and not calibrated vessel measurements. Outflow does not depict chamber blood volume with the new tubes; those values remain model readouts. Physical iPad usability/listening and actual Cursor review remain separate qualifications. No audio was regenerated. Original recordings and transcripts remain byte-identical.
