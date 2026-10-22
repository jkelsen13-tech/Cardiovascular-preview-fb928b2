# Contextual audio candidate, 2026-10-22

This private candidate implements the owner's corrected interaction requirement: explanations are available for the page or section the learner opens, and the learner chooses when to listen. It starts from recovery commit `fb928b2957a05c6ffe88e4c0a23a87abf2831a0f` (tree `5581172aa0c3b477ec5f0c26c12c6f3e9c48086c`). It has not been published or deployed.

## Interaction contract

- Opening a supported simulator or study-guide page prepares a related explanation, paused. Audio never starts merely because a page, section or recording is selected.
- Play/Pause, Replay and seek control only the explanation. Replay intentionally starts that recording from the beginning. The transcript and source remain available without playback.
- The learner operates the camera, anatomy selection, phase, simulator clock and all native controls. Audio never applies the original scene cues, changes a route, scrolls, focuses a control or adds a highlight.
- Manual interaction within the same page refreshes the related choices while current narration continues without pause/resume. A recording outside the new choices stays identified as the current recording. Choosing another recording explicitly loads it paused.
- Explicit navigation to a different page stops the previous recording and prepares the new page's first related explanation, paused. Leaving supported pages stops and unloads it. Nothing plays next automatically.
- Simulator ticks do not rotate the audio choices. An explicitly selected heart phase can determine choices; an automatically advancing phase cannot.
- No Guided/Explore takeover, Return to Guided control, automated-tour fallback or audio-owned saved simulator state is loaded. Existing historical storage is ignored and left untouched. Native manual simulator lessons remain native user controls.

## Content mapping

`guided-study/contextual-contexts.js` maps actual native state and the 19 existing ASPT study-path topic IDs to the unchanged lesson IDs. There is no separate audiobook catalog on the home menu.

| Current page or section | Related content |
| --- | --- |
| Heart v3 chamber, valve, vessel or conduction structure | M02 anatomy/flow, M03 pump mechanics, M04 conduction |
| Manually selected cardiac phase | Corresponding M03 filling, contraction, ejection or relaxation explanation |
| Heart microscope routes A–D | Valve/pump anatomy; wall/cell/myofibril/sarcomere; nodal/ventricular electrical physiology; coronary/capillary exchange, using the actual stage IDs |
| Respiratory structure and airway explorer stage | M05 anatomy, ventilation and gas exchange; selected M06 clinical physiology |
| Lead Placement Lab selected lead or landmark | Related M07 placement/lead concepts and M01 orientation |
| ECG Waves & Intervals selected wave/stage | Related M08 wave, interval and measurement explanations |
| ECG Rhythm Practice | M08 interpretation method and limits; audio does not choose a practice answer |
| ASPT foundation, blood, anatomy, muscle, circulation, disease, pressure, airway, respiration, conduction, cycle, instrument, waves, measure, limb, placement, prep, artifacts, rhythms | All 111 recordings distributed among these existing topics, including the M09–M14 rhythm and integrative content |

A topic can offer multiple relevant recordings. Terms search uses the matching existing study-path topic where present. Unsupported sections show no matching recording rather than inventing visual coverage. Mapping coverage does not certify that every clip fits every possible view of a topic.

## Preservation and media lifecycle

All 111 MP3 files, exact transcripts, lesson definitions, provenance manifests and the original 725 scene cues are unchanged. The cues are retained as historical data and never enacted by this player. Heart, lung, lead, ECG and ASPT native source/assets are unchanged. Both HTML entry pages load the same contextual player.

The player reads native getters and small structural panels; it does not call simulator adapters. Scoped visibility/section observers and manual input events update context, including completion of a delayed native microscope route. There is no animation loop, clock polling, persistent storage or view manipulation.

One selected same-origin MP3 is fetched in full and prepared as a Blob URL before Play becomes available. This gives seek a complete original source even on a static preview without Range support and keeps Play within the explicit user gesture. It uses the original compressed audio bytes, not generated audio. A new page or recording aborts the preceding preparation and increments a revision token; a delayed old result cannot replace or start the new recording. Replacement/disposal revokes the old URL. A failed preparation offers Reload, which retries paused. Loading consumes the selected file's bandwidth and temporary memory; playback on physical iPad/Safari remains to be checked.

## Narration compatibility

An internal independent reviewer read all 111 original transcripts and verified their hashes. No explicit promise that software moves the camera, navigates or pauses for the learner was found. The old runtime behavior was the central interaction mismatch. This is a text audit, not listening or clinical qualification, and it does not establish universal clip-to-view fit.

The unchanged audio still assumes some views or tasks. `contextual-compatibility.js` displays manual prerequisites on the relevant recordings:

| Recordings | Qualification or later work |
| --- | --- |
| M01.01 | Recommend later revision of the sequential course introduction to explain user-chosen contextual listening. |
| M03.03, M04.04, M05.06 | Filling, conduction-overlay colors and inspiration references require a user-selected view/phase; consider later standalone wording. |
| M02.01, M02.06, M04.01 | Chamber, wall-thickness or conduction view prerequisites. |
| M04.12, M09.06, M10.07, M14.07 | Optional user-led checkpoints/review spanning views, strips or topics. |
| M08.09 | Method explanation; no calibrated tracing/measurement tool is implied. |

No script or paid audio was regenerated. A later wording/audio pass requires separate scope; these notices do not claim the recordings have been rewritten.

## Verification

Run from the repository root with an existing local HTTP preview and preinstalled tools:

```sh
node tools/contextual-audio/verify.cjs
CARDIO_BASE_URL=http://127.0.0.1:8881/ python tools/contextual-audio/browser.py
CARDIO_BASE_URL=http://127.0.0.1:8881/ python tools/contextual-audio/lifecycle-browser.py
node tools/heart-v3/model.cjs
node tools/simulators/mechanics.cjs
```

The focused browser scripts use installed `/usr/bin/chromium` with its sandbox enabled. They create evidence outside the source checkout; `CONTEXTUAL_AUDIO_OUT` can override each script's output root. They use real original MP3s and native controls, without audio mocks. The lifecycle cases hold and release real requests to check delayed route/media completion; no replacement source is supplied.

The completed private pass recorded 46 passing UI/media checks and nine passing lifecycle checks, with no JavaScript or missing-asset errors. These include exact paused heart/lung state and camera preservation on playback, seek across old cues, uninterrupted narration during manual anatomy/camera/phase/start/pause controls, independent simulator clocks, topic/page policy, exact transcript, mobile-width controls, adapter-call guards, late route completion, stale media cancellation and object-URL cleanup. The CPU verifier checks all 111 MP3 hashes and transcript hashes, all recordings mapped to the actual study-path topics, old tour scripts absent and read-only native API use. Heart-model and respiratory-mechanics CPU suites passed (54 respiratory parameter/mode combinations).

Historical guards remain unchanged and visible. Running the unchanged teaching-clarity preservation gate against both recovery baseline and candidate yields the same 38 passes followed by the existing `simulation-core/module.js` fingerprint mismatch; that run stops there. Expected hash is `fe578b6c1602269799d4cd32762cbf34c7a6a2db03f9315cd96c591233807b4b`, while both sources contain `d2d45e06a2dcb6529fe96f01f0ad14b5977d22f02951cd3f371260bfaf826cc9`. No fingerprint was updated to manufacture a pass. Earlier reported 47-pass/six-historical-guard results are historical, not a new result of this pass. Old automated-tour behavior tests are preserved but do not define the corrected requirement.

The separate existing lead-placement verifier could not start its bundled Playwright headless-shell because that executable is absent. No browser was installed. The new focused browser suite did open and inspect the actual Lead Placement Lab using installed sandboxed Chromium; it does not replace every old lead-placement assertion.

Screenshots and media-element events establish cloud browser behavior only. This environment still has no actual sound-output monitor or display-presentation capture endpoint. Physical iPad/Safari listening, sound/display synchronization, full anatomical/clinical acceptance and actual Cursor review remain pending.

## Private handoff and next step

Keep this branch private until the owner reviews the corrected behavior. The original recovery branch, old public preview history, original main and original live site remain intact. This pass does not push, deploy, change settings or create new credentials.

After review and explicit publication authorization, update only the existing separate `jkelsen13-tech/Cardiovascular-preview-fb928b2` preview branch. Preserve its deliberate exclusion of the nine original workflow definitions so publishing the candidate cannot trigger unrelated original CI/deployment destinations. Verify hosted entry pages, contextual scripts and original audio hashes before iPad handoff. The cloud loopback URL is not a shareable iPad URL.

Suggested owner acceptance: open the heart simulator and play M02.01; change the chamber/camera and run/pause the heart while audio continues; manually choose ejection and confirm related M03.05 is offered without automatic view changes. Open Respiratory Simulator v2, select diaphragm and play M05.06; operate breathing controls yourself. Open ASPT circulation, play M02.08, then select disease and confirm M14 choices appear while current audio continues. Selecting another recording or opening another page should leave the new recording paused. Check Replay, seek, transcript and audible output on the physical iPad.
