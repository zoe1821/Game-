# LIFEVERSE — Roadmap and Workload

Status: **proposed, awaiting review.** Milestone 1 is complete except for that
review. Revised on 2026-11-15 to include the additional requirements (`A1`–`A10`,
`docs/requirements/02_additional_requirements.md`).

---

## 1. Honest workload estimate

### 1.1 What the combined requirements describe

The original brief asked for a life simulator with about thirty professions that
each play as their own game. The additional requirements add a full everyday-life
simulation, a dialogue system, a complete hospital management simulation, an
evolving world with businesses and news, animation, sound and music, expansion
packs, and a production pipeline. Taken together this is the scope of several
commercial games built by studios over years.

It will not all exist at the end of this roadmap, and no plan that claims otherwise
should be trusted. What changes with the new requirements is not that everything
becomes possible, but that **more systems must exist and be integrated before the
game counts as cohesive**, so the roadmap is longer and split into smaller verified
steps.

### 1.2 Depth tiers

To keep "implemented" honest, every feature is built to a declared depth:

| Tier | Meaning | Examples |
|---|---|---|
| **1 — Interactive** | Played as a scene: decisions, feedback, consequences, animation. | Consultations, conversations, arguments, job interviews, work shifts, management decisions, shopping for a meaningful gift. |
| **2 — Systemic** | Fully simulated with real trade-offs; steered through plans and choices; visible in presentation. | Sleep, hygiene, nutrition, commuting, chores, pet care, budgets, business lifecycle, waiting lists. |
| **3 — Ambient** | Simulated and observable, not directly steered. | Weather, news, the lives of distant NPCs. |

Daily self-care is Tier 2 by design (ARCHITECTURE §18.1): a routine you set, with
consequences you feel, and any day can be opened and played by hand. It is not
thirty thousand tooth-brushing minigames. If a specific item should be Tier 1,
that is an owner decision (§7).

### 1.3 Size

Estimates with wide error bars; content writing is the dominant uncertainty.

| Milestone | Code (lines) | Tests (lines) | Content items | Effort |
|---|---|---|---|---|
| 1 Architecture and tooling | — | — | documents, scripts | done |
| 2 Foundation and production base | ~6,000 | ~2,200 | ~60 | ●●●● |
| 3a People and conversation | ~7,000 | ~2,500 | ~500 | ●●●●●● |
| 3b Daily life | ~7,000 | ~2,500 | ~450 | ●●●●●● |
| 3c Education, economy, consequences | ~6,000 | ~2,200 | ~350 | ●●●●● |
| 4 Career framework and workflow | ~4,500 | ~1,800 | ~120 | ●●●● |
| 5a Psychiatry: clinical | ~7,500 | ~2,500 | ~350 | ●●●●●● |
| 5b Psychiatry: hospital operations | ~5,000 | ~1,800 | ~200 | ●●●● |
| 6a Hospital management, specializations, private practice | ~4,500 | ~1,500 | ~250 | ●●●● |
| 6b World and NPC depth | ~4,000 | ~1,500 | ~300 | ●●●● |
| 6c Two more careers | ~6,000 | ~2,000 | ~400 | ●●●●● |
| 7 Audiovisual, accessibility, onboarding, polish | ~6,000 | ~1,200 | ~400 + assets | ●●●●●● |
| 8 Test and release | ~1,000 | ~1,200 | — | ●●● |
| **Total** | **~64,000** | **~23,000** | **~3,400** | **~57 ●** |

This is roughly **double** the estimate made before the additional requirements
(~31,000 lines, ~27 ●). Each "●" is about one focused working session of the kind
that produced Milestone 1. Every content item is bilingual, so the number of written
strings is several times the item count.

After this roadmap, each additional career is estimated at 1–3 sessions when it
reuses existing kernels and 3–6 when it needs a new one (ARCHITECTURE §9.4).

---

## 2. Rules for every milestone and sub-milestone

### 2.1 Entry gate (A10)

Before work on a major module starts:

1. The full test suite passes on the current branch.
2. Every feature the module depends on is at least **TESTED** in the registry.
3. The dependency check is written into `DEVLOG.md`.

### 2.2 Definition of done

1. The game runs (headless and rendered under xvfb) without script errors.
2. `tools/run_tests.sh` passes; new functionality has tests.
3. Save/load is verified for everything added, including the determinism test.
4. **A playable build exists** for the milestone (exported by `tools/build.sh`,
   checked by launching it) and is kept as a CI artifact.
5. The feature registry is updated; nothing is VERIFIED without a recorded,
   reproducible procedure. `PROJECT_STATUS.md`, `DEVLOG.md`, `KNOWN_ISSUES.md` updated.
6. Screenshots of new screens are captured and reviewed, in Spanish and English.
7. Nothing previously working was removed or weakened; no test was relaxed to make
   room for content.
8. The next step's plan is restated in light of what was learned.

---

## 3. Milestones

### Milestone 1 — Research, architecture, tooling ✅ (pending review)

Environment inspected; Godot, Blender, export templates and Android SDK installed
by pinned scripts; technical assumptions tested with spikes; export to four
platforms and the Blender pipeline verified by committed scripts; architecture,
psychiatry design, UI direction, roadmap, requirements and feature registry written.
No game code.

### Milestone 2 — Playable foundation and production base

*A character is born, time passes, things happen, it all survives a restart — and
the project can be built, logged, measured and translated from day one.*

- Godot project, strict typing, layering test, test runner, run/screenshot scripts.
- `Simulation`, `WorldState`, commands, bus, queries; calendar and Continue;
  agenda; `Person` and family generation; aging, life stages, death.
- Condition/effect registries; event director v1; `ContentDB` with schemas and the
  **pack loader** (the base game loads as pack `base`); ~40 starter events.
- Save system v1: slots, atomic writes, backups and **recovery screen**, typed
  round-trips, RNG streams, determinism test, autosave, resume.
- **Production base (A9):** error logging to rotating files; performance benchmark
  with a budget table; `tools/build.sh` and packaging; CI workflow that tests and
  builds; version stamping; feature-registry check in the test run.
- **Options (A8), first cut:** Spanish and English complete; text scale; animation
  intensity; settings persistence. `AudioService` with buses and interface sounds.
- UI: theme tokens and kit, main menu and slots, minimal creation, dashboard, event
  dialog, timeline, settings — portrait and wide layouts.

**Acceptance:** start a life → play to old age and death → quit anywhere → reload
exactly; a bot completes 200 lives headless with zero errors; builds for Linux,
Web, Windows and Android are produced by one command.

### Milestone 3 — Life systems (three verified steps)

**3a — People and conversation (A2, B2, B3).** Full character creation with
procedural portrait; **character rig and facial expressions**; relationships,
memories, reputation, gossip; the **conversation engine** (context-sensitive topics,
approaches, emotional reactions, secrets, arguments and reconciliation, friendship
and romance stages); NPC agents v1 with **NPC-initiated interactions**; family:
dating, marriage, divorce, pregnancy, children, death, inheritance, succession.
People, profile, interaction and family-tree screens.

**3b — Daily life (A1).** Needs; routines and the day view; activities; shopping
and inventory; home and chores; transport; pets; hobbies and clubs; trips;
birthdays, holidays and occasions; place scenes with **day/night and weather** and
ambience sound.

**3c — Education, economy, consequences (B7, B8, B9, A5 first cut).** School
stages, courses, exams, grades, university applications, tuition, degrees and
qualifications; accounts, ledger, tax, loans, rent, housing; localities and
businesses v1; news v1; storylines and long-fuse consequences; relevance-weighted
director and pacing.

**Acceptance:** a relationship formed at school demonstrably changes events decades
later (scripted test); an NPC starts a meaningful conversation on their own; a year
of routine life and a hand-played day produce the same kinds of effects; a full
life through university is playable in both languages; generational continuation
works and is saved.

### Milestone 4 — Career framework and complete professional workflow (B4, A3)

- `CareerHost`: vacancies, applications, **interviews as conversations**, offers and
  rejections, contracts, schedules, colleagues and supervisors, professional
  conflicts, reviews, promotion, resignation, dismissal, certifications and
  licences, specializations, retirement.
- `CareerModule` contract, context, manifest schema, registry, conformance tests.
- `ShiftSession` and `shift_clock`; played and auto-resolved shifts on one code
  path; mid-shift save and resume. Career dashboard and workspace host.
- `Business` ownership base for entrepreneurship and private practice.
- A deliberately simple but real **reference career** (proposal: teacher).
- Economy v2: mortgages, property, investments, retirement savings.

**Acceptance:** qualify → apply → interview → be hired or rejected → work played and
auto-resolved shifts → be reviewed → be promoted, resign or be dismissed → retire.

### Milestone 5 — Psychiatry (two verified steps)

**5a — Clinical (B5).** Kernels `case_file`, `interview` profile, `inference`;
patient generation and hidden truth; chart with provenance and comparison;
consultation; formulation; treatment; disposition; follow-up; daily progression;
supervision, documentation, KPIs, exams; ranks trainee → resident → attending →
senior specialist; adult specialization; medical education path; consultation
scenes with patient body language. Solver, balance and parity tests.

**5b — Hospital operations (A4).** `institution` kernel; departments; doctors and
nurses as persistent staff with a rota; waiting lists; admissions, transfers and
discharges; emergencies; institution-wide documentation; **privacy and
confidentiality mechanics**; interdepartmental requests; hospital map and all areas.

**Acceptance:** the first playable slice of `PSYCHIATRY_DESIGN.md` §11; a multi-year
career with returning patients whose histories and treatment progress survive
sessions; a full hospital week runs with the player absent; a privacy breach is
detectable by audit.

### Milestone 6 — Management, world depth, more careers (three verified steps)

**6a — Hospital management.** Budgets, equipment and supplies, quality assessments
and inspections; department director and hospital administrator ranks; child,
forensic and geriatric specializations; private practice.

**6b — World and NPC depth (A5, B3).** NPC agents v2 (grudges, reconciliation,
NPC-driven storylines); business lifecycle and job market tied to the economic
cycle; social calendar; news v2; deeper generational effects; save migrations
exercised on real saves from Milestones 2–5; compaction.

**6c — Two more careers.** Proposal: **detective** (reuses case_file, conversation
and inference; adds scene work and a lead board) and **entrepreneur** (adds the
`project` kernel and a company model on `Business`).

### Milestone 7 — Audiovisual, accessibility, onboarding, polish (A6, A8, A9)

- Animation set completed; environments detailed; ambient music; full sound pass
  (with owner listening tests); interface motion.
- Accessibility complete: colour modes, remappable controls, captions and subtitle
  options, audio options; difficulty and gameplay customization.
- Tutorials and onboarding; achievements and the cross-life profile.
- Performance profiling on long saves; balance pass from soak data.
- A small **expansion pack** built and loaded as proof of the content pipeline.
- **Decision point:** optional 3D workspace scenes.

### Milestone 8 — Comprehensive testing and release build

Full regression, soak (thousands of lives), save-compatibility and UI-smoke runs;
release builds and packages for the chosen platforms, each launched or checked;
player documentation; version tag.

---

## 4. Sequencing rationale

- Save/load, logging, builds and translation come first because retro-fitting them
  is where projects like this fail.
- The conversation engine comes before careers because interviews and clinical
  consultations are built on it.
- Daily life comes before careers because a job has to compete for the hours of a
  real day.
- A simple reference career precedes psychiatry so the contract is shaped by two
  users.
- Hospital operations follow the clinical loop so there is something worth managing.
- Breadth (more careers) and the heavy audiovisual pass come after one career is deep
  and the systems they decorate are stable — "never sacrifice stability to add content".

---

## 5. What can and cannot be verified in development

Can: all logic headless; rendered screens by screenshot; scripted UI interaction;
Linux and Web builds by running them; structure and signing of Windows and Android
builds.

Cannot: **sound of any kind**, real-GPU performance, touch and gamepad feel,
screen-reader behaviour, running the Windows or Android builds, and whether it is
fun. Those need the owner playing builds. The roadmap assumes a short owner playtest
at the end of Milestones 2, 3a, 3b, 5a, 6a and 7, and an owner listening test for
every audio pass.

---

## 6. Running it yourself

From Milestone 2, every milestone produces builds for Linux, Windows, Web and
Android. Alternatively install the Godot 4.7.2 editor, open
`lifeverse/game/project.godot` and press Play.

---

## 7. Open decisions for the project owner

Defaults are used if no preference is given.

| # | Decision | Default | Why it matters |
|---|---|---|---|
| 1 | **Existing Unity prototype**: keep in place / move to `legacy/` / remove | Keep in place, untouched | Only the owner can retire it. |
| 2 | **Which build will you play on?** | All four are produced | It decides where testing effort goes; Windows and Android cannot be run in development. |
| 3 | **Languages** | **Decided:** Spanish and English, both complete at every milestone; Spanish authored first. Technical documents stay in English with `RESUMEN.md` in Spanish | Say if the documents should be translated too. |
| 4 | **Time model** | Continue-until-interrupt; week/month/year stride; 336-day year; routine / day / moment zoom levels | Defines the feel of the whole game. |
| 5 | **Depth of daily self-care** | Tier 2: routines with consequences, any day playable by hand | Alternative: specific activities as Tier 1 scenes — say which. |
| 6 | **Clinical naming** | Plain descriptive condition labels; abstract treatment classes; fictional country and law | Keeps the game clear of real-world medical guidance. |
| 7 | **Tone and age rating** | Mature themes handled seriously and non-graphically; content settings | Affects all writing. |
| 8 | **Careers for 6c** | Detective and entrepreneur | Any from the brief can be substituted. |
| 9 | **Reference career for 4** | Teacher | Must be simple yet real. |
| 10 | **Audio sources** | Scripted, generated audio plus CC0 material with recorded licences; owner approves by ear | Alternative: owner supplies or commissions music and sound. |
| 11 | **Windows installer** | Portable zip only | An installer needs Windows tooling not available in development. |
