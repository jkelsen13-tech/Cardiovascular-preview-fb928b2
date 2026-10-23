# Course-focused controls

This presentation pass retains every simulation, the original physiology models,
all original recordings/transcripts, ECG paper measurement and rhythm questions.
It replaces technical student-facing tuners with existing defaults rather than
introducing another advanced dashboard.

- Heart: one eight-view selector, manual transport/phase/labels/reset, anatomy and
  connected routes. One ECG accompanies conduction; nodal/working-cell action
  potentials stay in their local lesson. The six-plot mechanics dashboard,
  independent coefficients, layer/leader and duplicate signal/view controls are
  removed. SV/CO/EF and loading concepts remain; the existing v2 calculator stays.
- Lungs: one ordinary breathing clock, retained airway/alveolar/exchange lessons,
  capnogram and positive-pressure comparison. Technical layer/context/leader,
  duplicate rate/depth tuners and four mechanics curves are removed. Native
  fullscreen retains its own core transport.
- Lead placement: retain guided/explore/cards/quiz, landmarks, colors, lead types,
  reset/zoom/touch controls; remove layer/material and duplicate display switches.
- ECG waves, interval/rate measurement, paper calibration, source rhythm strips,
  course questions, study guide and original audio player are unchanged.

The supplied course review mapped these choices to the January 2026 ASPT guide
pp3–9 and combined slide PDF pp48–105 (respiration/capnography),106–216 (heart and
conduction),227–285 and366–452 (ECG/measurement),346–362 (action potentials),
and453–911 (rhythms, blocks, pacing, ischemia). SV/CO/EF and loading concepts are
on pp128–131. These are PDF page references supplied by the course reviewer;
private PDFs and their diagrams are not redistributed. Course alignment does
not establish current exam weighting, an optimal learning layout, or exam success.

`browser.py` uses existing Playwright plus installed, sandboxed Chromium. Set
`CARDIO_BASE_URL` and `COURSE_CONTROLS_OUT` to an existing preview and private
artifact directory. It exercises real UI/media without mocking the audio or
changing model time via an audio adapter. The output is browser evidence, not
physical listening, Safari/iPad or clinical/anatomical validation.

Historical tests asserting the removed dashboards/selectors remain historical
contracts. Bundled-browser legacy harnesses require a missing headless shell in
the cloud workspace; the installed-browser acceptance reports that distinction.
