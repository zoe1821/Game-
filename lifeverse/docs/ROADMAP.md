# LIFEVERSE — Roadmap and Workload

Status: **proposed, awaiting review.** Milestone 1 is complete except for that review.

---

## 1. Honest workload estimate

The full brief — a complete life simulator plus about thirty professions that each
play as their own game — is the output of a studio over years. It will not exist at
the end of this roadmap, and no plan that claims otherwise should be trusted.

What this roadmap delivers is the part that makes the rest possible and is worth
playing on its own:

- a complete, persistent, save-anywhere life simulation;
- the career framework and reusable gameplay kernels;
- **one profession at real depth (psychiatry)**;
- two further professions proving the framework generalises;
- a tested, exported desktop build.

Size estimates (GDScript lines exclude tests and data; all figures are estimates
with wide error bars, and content writing is the dominant uncertainty):

| Milestone | Code (lines) | Tests (lines) | Content items | Relative effort |
|---|---|---|---|---|
| 1 Architecture | — | — | 5 documents | done |
| 2 Foundation | ~4,500 | ~1,500 | ~40 | ●●● |
| 3 Life systems | ~6,000 | ~2,000 | ~250 (events, storylines, NPC actions, programmes) | ●●●●● |
| 4 Career framework | ~3,000 | ~1,200 | ~40 | ●●● |
| 5 Psychiatry | ~7,500 | ~2,500 | ~300 (profiles, findings, questions, treatments, events) | ●●●●●● |
| 6 NPC depth + more careers | ~6,000 | ~2,000 | ~300 | ●●●●● |
| 7 Polish & accessibility | ~3,000 | ~800 | art/motion/locale | ●●●● |
| 8 Test & release | ~800 | ~1,000 | — | ●● |
| **Total** | **~31,000** | **~11,000** | **~900** | |

Each "●" is roughly one focused working session of the kind that produced this
milestone. Milestones 3, 5 and 6 are the ones most likely to overrun, because their
quality depends on the volume and care of written content, not on code.

After this roadmap, each additional career is estimated at 1–3 sessions when it
reuses existing kernels and 3–6 when it needs a new one (see ARCHITECTURE §9.4).

---

## 2. Milestone definition of done (applies to every milestone)

1. The game runs (headless and rendered under xvfb) without script errors.
2. `tools/run_tests.sh` passes; new functionality has tests.
3. Save/load is verified for everything added, including the determinism test.
4. `PROJECT_STATUS.md`, `DEVLOG.md` and `KNOWN_ISSUES.md` are updated; incomplete
   items are listed as incomplete.
5. Screenshots of new screens are captured and reviewed.
6. Nothing previously working was removed without being recorded.
7. The next milestone's plan is restated in light of what was learned.

---

## 3. Milestones

### Milestone 1 — Research and architecture ✅ (pending review)

Environment inspected; engine pinned and installed reproducibly; technical
assumptions tested with spikes; architecture, psychiatry design, roadmap, status,
dev log and known-issues documents written. No game code.

### Milestone 2 — Playable life-simulation foundation

*Goal: a character is born, time passes, things happen, and it all survives a restart.*

- Godot project skeleton, strict-typing settings, layering test, test runner,
  `run_tests.sh`, `run_game.sh`, `screenshot.sh`.
- `Simulation`, `WorldState`, `Command`/`CommandResult`, `SimBus`, `Queries`.
- `GameDate`, `TimeSystem` with Continue-until-interrupt and stride control; agenda.
- `Person` model, seeded person/family generator, aging, life stages, death.
- Condition and effect registries; `EventDirector` v1 (pulse + scheduled events,
  role binding, choices, outcomes, history).
- `ContentDB` with schema validation; ~30 starter events across life stages.
- Save system v1: slots, atomic write, backups, typed round-trips, RNG streams,
  determinism test, autosave, resume.
- UI: theme tokens and kit basics, main menu/slots, minimal character creation,
  dashboard, event dialog, timeline, settings shell.
- Export smoke test for the chosen desktop target (risk #12).

**Acceptance:** start a life → play to old age and death with events and choices →
quit at arbitrary points → reload exactly. A bot completes 200 lives headless with
zero errors.

**Explicitly not in M2:** relationships beyond the family list, education, money
beyond a single balance, careers.

### Milestone 3 — Character creation, aging, education, relationships, consequences

- Full character creation (name, appearance with procedural portrait, gender,
  personality, background/family circumstances).
- Relationship system: opinions from memories, decay, kinds, reputation, gossip.
- Family system: partners, dating, marriage, divorce, pregnancy, children,
  household, death, inheritance, **succession to an heir**.
- NPC agents v1 (Tier A monthly decisions, Tier B yearly lives, promotion/demotion).
- Storylines and long-fuse consequences; relevance-weighted director; pacing.
- Education: school stages, courses, grades, exams, student relationships,
  university applications, tuition/loans, degrees and qualifications.
- Economy v1: accounts, ledger, recurring items, tax, loans, rent, housing.
- Weekly time-budget plan.
- UI: people list, character profile, interaction, family tree, education, finance.
- ~250 content items including the worked "university connection" storyline.

**Acceptance:** a relationship formed in school demonstrably changes events decades
later (scripted test); a full life through university is playable; generational
continuation works and is saved.

### Milestone 4 — Professional career framework

- `CareerHost`: job market, applications, interviews, contracts, ranks, schedules,
  pay, reviews, promotion/dismissal, reputation, licences, retirement.
- `CareerModule` contract, `CareerContext`, manifest schema, registry, conformance
  test suite.
- `ShiftSession` + `shift_clock` kernel; agenda integration; interactive vs.
  auto-resolved shifts sharing one code path; mid-shift save/resume.
- Career dashboard UI and workspace host.
- A small **reference career** used as the contract's proving ground (candidate:
  *school teacher's assistant → teacher* at modest depth, or a clerical job) — real
  but deliberately simple, clearly labelled as such.
- Economy v2: mortgages, property purchase, investments, retirement savings.

**Acceptance:** get qualified → apply → get hired → work played and auto-resolved
shifts → be reviewed → be promoted or dismissed → retire; all persisted.

### Milestone 5 — Psychiatry career module

- Kernels: `case_file`, `interview`, `inference`.
- Patient generation, hidden truth, chart with provenance and comparison,
  consultation, formulation, treatment, disposition, follow-up, daily progression.
- Hospital map and all listed areas with their workspaces.
- Supervision, documentation, KPIs, exams; ranks **trainee → resident → attending →
  senior specialist** with rank-specific play; adult specialization.
- Psychiatry event pack and storylines; staff as persistent NPCs.
- Solver/balance/parity tests from `PSYCHIATRY_DESIGN.md` §10.
- Medical education path (medicine degree, licence) so the career is reachable from
  birth in normal play.

**Acceptance:** the first playable slice in `PSYCHIATRY_DESIGN.md` §11, plus a
multi-year career with returning patients, all tests in §10 green.

**Deferred to M6 (stated now so it is not a surprise):** the two management ranks
(department director, hospital administrator) and the child, forensic and geriatric
specializations.

### Milestone 6 — Advanced NPCs, persistence hardening, more careers

- Psychiatry management ranks (`org` kernel) and remaining three specializations.
- NPC agents v2: richer goals, grudges and reconciliation, NPC-initiated storylines,
  cross-links between professional and personal circles.
- World events system (economic cycle, policy changes) feeding jobs, housing, hospital.
- Two additional career modules chosen to stress different kernels. Proposal:
  **detective** (reuses case_file/interview/inference; adds lead board and scene
  work) and **entrepreneur** (adds `project` and company model, ties into economy).
- Save migrations exercised with real golden saves from M2–M5; size compaction.

### Milestone 7 — Polish, performance, accessibility

- Visual pass: motion, transitions, iconography, portraits, charts, empty states.
- Accessibility: scaling, high contrast, reduce motion, full keyboard/gamepad,
  accessible names; content settings.
- Localization pass (EN + ES if confirmed).
- Onboarding and contextual help; balance pass using soak-test telemetry.
- Performance profiling on long saves.
- **Decision point:** optional 3D workspace scenes (Blender is installed and the
  export pipeline verified; build only if 2D is complete and the result would be
  an improvement).

### Milestone 8 — Comprehensive testing and release build

- Full regression, soak (thousands of lives), save-compatibility and UI-smoke runs.
- Export templates; release builds for the chosen platforms; build verification by
  launching the exported binary.
- Player-facing README, known-issues list, version tag.

---

## 4. Sequencing rationale

- Save/load and determinism come in M2, before there is much to save, because
  retro-fitting persistence into a simulation is where projects like this fail.
- The event engine comes before relationships and careers because they all express
  consequences through it.
- A deliberately simple reference career precedes psychiatry so the framework's
  contract is shaped by two real users, not designed around one.
- Breadth (more careers) comes only after one career is genuinely deep.

---

## 5. What I can and cannot verify in this environment

Can: all logic headless; rendered screens via xvfb screenshots; scripted UI
interaction; Linux export launch (once templates are downloaded).

Cannot: audio, real-GPU performance, touch and gamepad feel, screen-reader behaviour,
Windows/macOS/Android runtime behaviour, and — most importantly — whether it is
*fun*. Those need you playing builds. The roadmap assumes a short playtest by the
project owner at the end of Milestones 2, 3, 5 and 7.

---

## 6. Running it yourself

Until Milestone 8 produces exported builds, playing requires the Godot 4.7.2 editor
(free, ~80–150 MB): open `lifeverse/game/project.godot` and press Play. From
Milestone 2 onward the repository will also contain run scripts and, if useful,
intermediate exported builds can be produced earlier on request.

---

## 7. Open decisions for the project owner

Defaults will be used if no preference is given.

| # | Decision | Default | Why it matters |
|---|---|---|---|
| 1 | **Existing Unity prototype** in this repo: keep in place / move to `legacy/` / remove from this branch | Keep in place, untouched | Rule "never silently remove functionality"; only the owner can retire it. |
| 2 | **Target platforms** | Desktop first (Windows + Linux; macOS unsigned), layouts kept mobile-capable | The Unity prototype targeted Android landscape. Android/touch-first changes UI density and testing from M2. |
| 3 | **Languages** | English text now, all strings keyed; Spanish added in M7 | Existing docs are Spanish. Say if Spanish should be primary or simultaneous. |
| 4 | **Time model** | Continue-until-interrupt with week/month/year stride; 336-day year | Defines the feel of the whole game; cheap to change now, costly later. |
| 5 | **Clinical naming** | Plain descriptive condition labels; abstract treatment classes; fictional country and law | Satisfies "fictional, not real-world guidance". Alternative: fully invented terminology. |
| 6 | **Tone and age rating** | Mature themes handled seriously and non-graphically; content settings | Affects event writing from M2. |
| 7 | **Second/third careers for M6** | Detective and entrepreneur | Chosen to exercise different kernels; any from the brief can be substituted. |
| 8 | **Reference career for M4** | Teacher (simple first version, deepened later) | Needs to be simple yet real; alternatives welcome. |
