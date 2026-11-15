# LIFEVERSE — Technical Architecture

Status: **proposed, awaiting review** (Milestone 1). No game code exists yet.
Companion documents: [`PSYCHIATRY_DESIGN.md`](PSYCHIATRY_DESIGN.md) (first career module),
[`UI_DIRECTION.md`](UI_DIRECTION.md) (interface reference and original visual direction),
[`ROADMAP.md`](ROADMAP.md) (milestones, workload), [`DEVLOG.md`](DEVLOG.md),
[`KNOWN_ISSUES.md`](KNOWN_ISSUES.md), [`../PROJECT_STATUS.md`](../PROJECT_STATUS.md).

Every statement in §2 marked *verified* was tested in this environment on 2026-11-15.
Everything else in this document is design, not a claim about working software.

---

## 1. Vision in one paragraph

LIFEVERSE is a persistent life simulation in which the player lives one character's
life from birth to death (and on through their descendants), and in which **each
profession is a playable simulation of its own** rather than a "Work" button. The
player advances a calendar, makes life decisions, and — when employed — actually
works shifts inside a profession-specific workspace: interviewing patients, reading
charts, forming hypotheses, making decisions and living with the outcomes. The life
simulator and the professional simulators share one world: the same people, the same
money, the same calendar, the same memory of what happened.

Three properties drive every architectural decision below:

1. **One world state.** A patient is a person in the world, not a row in a minigame.
   A colleague can become a spouse; a decision at work can cost a friendship.
2. **Hidden truth, discovered evidence.** Professional play is about finding out what
   is true from incomplete, sometimes unreliable information — never about the game
   revealing the answer.
3. **Content is data.** Events, cases, questions, careers and NPC behaviours are JSON
   interpreted by a small set of engines, so adding the 400th event does not touch
   engine code.

---

## 2. Environment findings (verified)

| Item | Finding |
|---|---|
| Repository | **Not empty.** Contains a Unity 2022.3.21f1 C# project, "Psychiatric Hospital Simulator" V0.2 (22 scripts, ~1,500 lines, 3 JSON data files, Spanish docs). See §3. |
| Godot | Not preinstalled. Current stable is **4.7.2** (official download page). Installed and pinned via `lifeverse/tools/install_godot.sh` (SHA-256 checked); `godot --version` → `4.7.2.stable.official.ed1daf0bf`. |
| Headless execution | Works: `godot --headless --path <proj> --script x.gd` and headless scene runs. |
| Rendering | Works under `xvfb-run` with `--rendering-driver opengl3` (llvmpipe software GL). A Control scene with a tween rendered and was captured to PNG. UI can therefore be screenshot-verified in this container. No audio device (dummy driver). |
| Blender | Not preinstalled. **5.3.0** installed and pinned via `lifeverse/tools/install_blender.sh` (official SHA-256 checked). Runs headless (`blender -b --python`). Verified end to end: a scripted mesh with material and keyframe animation exported to `.glb` and imported by Godot 4.7.2 with mesh, material and animation intact; Cycles CPU render to PNG works. No GPU here, so EEVEE/viewport rendering is untested. Still **not needed before Milestone 7**. |
| SQLite | No `sqlite3` binary. Godot has no built-in SQLite; it needs a third-party GDExtension. |
| Third-party GitHub repos | Blocked by this session's proxy (HTTP 403 for GUT and godot-sqlite archives). They could be attached on request, but see dependency policy §14. |
| Export templates | Download URL for 4.7.2 templates is reachable. **Not yet downloaded or tested** (needed in Milestone 8). |
| Other tools | Python 3.13, Node 22, ImageMagick, ffmpeg, git-lfs, xvfb. 4 cores, 15 GB RAM. |

Spike results (throwaway projects, not committed) that shaped the design:

| Assumption tested | Result | Consequence |
|---|---|---|
| JSON round-trips numbers faithfully | **No.** `JSON.parse_string` returns every number as `float`; `42` → `42.0`; 64-bit ints lose precision. | Models deserialize through explicit typed `from_dict()`; 64-bit values are stored as strings (§11). |
| RNG state survives a JSON save | **No** as a number (state `-4117932630476122483` came back altered). **Yes** as a decimal string: the resumed stream was bit-identical. | RNG seeds/states are saved as strings. Determinism across save/load is testable. |
| Autoloads exist in `--script` mode | **No** — not present at `SceneTree._init`. They exist in scene-run mode, including headless. | The simulation core must not reference autoloads (§5). Tests run as a headless scene. |
| Runtime plugin loading | `load(path_from_json).new()` + `is BaseClass` check works; typed `Dictionary[StringName, Callable]` handler registries work. | Basis of the career plugin and effect/condition registries (§8, §9). |
| Atomic save write | `store → rename_absolute` works; ZSTD-compressed files round-trip. | Save write protocol in §11. |
| Simulation cost | 2,000 NPC records × 80 ticks: 38 ms. Stringify+parse of 2,000 small records: 6 ms. | The NPC budget in §7.4 has ample headroom. |
| Engine API facts | Strict-typing warnings (`untyped_declaration`, `unsafe_*`) exist as project settings; `Control.set_accessibility_name` and `DisplayServer.accessibility_screen_reader_active` exist in 4.7.2; stretch settings exist. | Coding standards §15, accessibility §12.4. |

Because 4.7.2 is newer than much published Godot material, the rule for this project
is: **an API is "verified" only when the pinned engine accepts it** (`ClassDB`
introspection, `--doctool` output, or a passing test) — not because a tutorial says so.

---

## 3. The existing Unity project

The repository's `Assets/`, `Packages/`, `ProjectSettings/`, `README.md` and
`DESIGN.md` are a working Unity prototype of a *hospital management tycoon* (build
rooms on a grid, hire staff, route patients). It is a different game from LIFEVERSE
(you own a hospital vs. you live a life and are employed in one) on a different
engine and language, so its code cannot be reused directly.

Decision taken for Milestone 1 (non-destructive, reversible):

- **Nothing in the Unity project is modified, moved or deleted.**
- LIFEVERSE lives entirely under `lifeverse/`.
- What carries over is design knowledge, credited in `PSYCHIATRY_DESIGN.md`: the
  hidden patient model (DESIGN.md §5, §20), separation of symptoms / observations /
  history / tests / diagnosis / treatment / evolution (§27), the "diagnosis is never
  shown automatically" rule (§9), correctable errors (§21), and the room list.

Whether to keep the Unity prototype in place, archive it under `legacy/`, or drop it
from this branch is **an open decision for the project owner** (see ROADMAP §7).

---

## 4. Technology decisions

| Topic | Decision | Alternatives considered | Why |
|---|---|---|---|
| Engine | Godot **4.7.2 stable**, pinned | Latest-at-build-time | Reproducibility; the test suite is the upgrade gate. |
| Language | GDScript, statically typed, warnings-as-errors for untyped declarations | C# (.NET build) | Brief requires GDScript; single toolchain; no .NET export complications. Measured performance is far above need. |
| Renderer | Compatibility (OpenGL) | Forward+ / Mobile | The game is 2D UI; Compatibility runs everywhere including this container, low-end PCs, Android and Web. Optional 3D scenes (§12.5) are small enough for it. |
| Content format | **JSON** files, schema-validated at load | Godot `Resource` (.tres) | Content is authored and linted as text, diffed in review, generated by tools, and readable by tests without the editor. `Resource` is used only for engine-native assets (themes, scenes, fonts, icons). |
| Runtime state | Plain typed GDScript objects (`RefCounted`) with `to_dict()/from_dict()` | `Resource` + `ResourceSaver` | `ResourceSaver` saves can execute embedded scripts on load (unsafe for save files) and have no migration story. Explicit dicts give versioned migrations (§11). |
| Persistence | Versioned JSON documents, ZSTD-compressed, atomic writes, rolling backups | SQLite via GDExtension | The whole world fits in memory (a few MB); saves are snapshots, not queries. SQLite would add a native third-party binary per export platform. Revisit only if a save exceeds ~50 MB or needs partial loading (§11.6). |
| Tests | Small in-repo test runner (headless scene) | GUT, gdUnit4 | Zero external dependency; the core is engine-light pure logic. The runner's surface is ~150 lines. Can be swapped for GUT later without rewriting tests' intent. |
| 3D / Blender | Optional, deferred to Milestone 7, behind a clean seam. Pipeline when used: `.blend` sources → scripted headless export → `.glb` committed and imported by Godot (verified, §2) | 3D-first workspaces; Godot's direct `.blend` import | The brief makes 3D optional. Depth of simulation and UI quality come first; a hollow 3D hospital would violate "no decorative features". Committing `.glb` means running or testing the game never requires Blender. |
| Localization | All player-facing text via translation keys from day one (Godot `TranslationServer`, CSV) | Hard-coded English | Retro-fitting localization is expensive; existing project docs are Spanish, so EN + ES is a likely requirement. |

---

## 5. Layered architecture

```
┌──────────────────────────────────────────────────────────────────────────┐
│ UI layer            scenes + view scripts (Control). No game rules.       │
│  ui/screens, ui/kit, careers/*/ui                                         │
│        │ reads via Queries            │ acts via Commands                 │
├────────▼──────────────────────────────▼──────────────────────────────────┤
│ App layer           autoload services: Game (session), SaveService,       │
│  app/               Settings, Router, Audio, Localization                 │
│        │ owns exactly one Simulation instance                             │
├────────▼─────────────────────────────────────────────────────────────────┤
│ Simulation core     pure logic, RefCounted only, no Node, no autoload,    │
│  core/              no UI. Deterministic. Runs headless in tests.         │
│   Simulation ─ WorldState ─ Systems ─ EventDirector ─ CareerHost          │
│        ▲ registers ops / predicates / events / agents                     │
├────────┴─────────────────────────────────────────────────────────────────┤
│ Career plugins      careers/<id>/{career.json, module.gd, sim/, data/}    │
├──────────────────────────────────────────────────────────────────────────┤
│ Content             data/**/*.json  (events, storylines, names, economy,  │
│                     education, npc actions, …)                            │
└──────────────────────────────────────────────────────────────────────────┘
```

Dependency rules (enforced by a test that scans `preload`/`load`/class references):

1. `core/` never references `app/`, `ui/`, or any `careers/*/ui`.
2. `careers/<id>/sim` references `core/` only. `careers/<id>/ui` references its own
   `sim`, `ui/kit` and `app/`.
3. Career modules never reference each other. Cross-career effects go through the
   world (people, memories, flags, money).
4. UI never mutates `WorldState`. It sends a **Command** and re-renders on signals.

### 5.1 The Simulation object

`Simulation` is the facade for the whole core. The app layer holds one instance;
tests create as many as they want.

```gdscript
class_name Simulation extends RefCounted

var world: WorldState          # the single source of truth (plain data)
var bus: SimBus                # typed signals: date_advanced, event_presented, ...
var content: ContentDB         # immutable loaded definitions
var rng: RngStreams            # named deterministic streams

func execute(cmd: Command) -> CommandResult   # the only way to change the world
func query() -> Queries                       # read-only helpers for UI/tests
func to_dict() -> Dictionary                  # complete save payload
static func from_dict(d: Dictionary, content: ContentDB) -> Simulation
```

**Commands** are small data objects (`{type, params}`), e.g. `advance_time`,
`choose_event_option`, `interact_with_person`, `apply_to_program`, `begin_shift`,
`shift_action`, `transfer_money`. `execute()` validates, mutates, emits signals, and
returns what changed (or a typed refusal with a reason the UI can show). This gives
one choke point for validation, autosave triggers, an optional command log for bug
reproduction, and headless bots that play the game through the same door the UI uses.

### 5.2 Systems

A **System** is a stateless service operating on `WorldState`. Each declares the
cadences it wants (`daily`, `weekly`, `monthly`, `yearly`) and the commands, effect
ops and condition predicates it provides.

| System | Owns (state section) | Responsibility |
|---|---|---|
| `TimeSystem` | `clock`, `agenda` | Calendar, advancing, interrupts, scheduling. |
| `PersonSystem` | `people` | Creation/generation, aging, life stage, attributes, death. |
| `FamilySystem` | `families`, `households` | Kinship graph, pregnancy, birth, marriage, divorce, inheritance, succession. |
| `RelationshipSystem` | `relationships`, `memories` | Opinions from memories, decay, status changes, reputation, gossip. |
| `NpcAgentSystem` | (uses `people`) | Goal-driven NPC decisions and coarse off-screen lives. |
| `EducationSystem` | `education` | Enrolment, terms, grades, exams, applications, qualifications. |
| `EconomySystem` | `economy` | Accounts, ledger, recurring items, tax, loans, property, investments, market cycle. |
| `CareerHost` | `careers` | Job market, contracts, ranks, reviews, promotions; hosts career plugins. |
| `EventDirector` | `events` | Selecting, binding, presenting and resolving events and storylines. |
| `WorldEventSystem` | `world_context` | Macro state (economic cycle, policy changes, notable world events). |

Systems talk to each other only through (a) `WorldState` data they are documented to
read, (b) effect ops, and (c) `SimBus` signals. No system calls another system's
private methods.

---

## 6. Project directory structure

```
Game-/                              (repository root)
├── Assets/ Packages/ ProjectSettings/ DESIGN.md      ← existing Unity prototype (untouched)
├── README.md                                          ← points to both projects
└── lifeverse/
    ├── README.md
    ├── PROJECT_STATUS.md
    ├── docs/
    │   ├── ARCHITECTURE.md  PSYCHIATRY_DESIGN.md  ROADMAP.md
    │   ├── DEVLOG.md  KNOWN_ISSUES.md
    │   └── content/                 authoring guides: events, storylines, careers
    ├── tools/
    │   ├── install_godot.sh         pinned engine installer
    │   ├── run_tests.sh             import + headless test run, exit code = result
    │   ├── run_game.sh              run under xvfb / desktop
    │   ├── screenshot.sh            capture named screens to PNG for review
    │   └── lint_content.py          optional fast JSON schema pre-check
    └── game/                        ← Godot project root (project.godot)
        ├── project.godot
        ├── app/                     autoloads
        │   ├── game.gd              session: holds Simulation, new/load/quit flow
        │   ├── save_service.gd
        │   ├── settings.gd          video, audio, accessibility, language
        │   └── router.gd            screen stack + transitions
        ├── core/
        │   ├── simulation.gd  world_state.gd  command.gd  sim_bus.gd  queries.gd
        │   ├── util/                game_date.gd  rng_streams.gd  ids.gd  weighted.gd
        │   ├── content/             content_db.gd  schema.gd  validators/
        │   ├── rules/               condition_evaluator.gd  effect_executor.gd  text_resolver.gd
        │   ├── time/                time_system.gd  agenda.gd
        │   ├── people/              person.gd  person_system.gd  generator.gd  appearance.gd
        │   ├── family/              family_system.gd  household.gd  succession.gd
        │   ├── social/              relationship.gd  memory.gd  relationship_system.gd  reputation.gd
        │   ├── npc/                 npc_agent_system.gd  goal.gd  lod.gd
        │   ├── education/           education_system.gd  enrolment.gd  qualification.gd
        │   ├── economy/             economy_system.gd  ledger.gd  account.gd  loan.gd  property.gd  market.gd  tax.gd
        │   ├── events/              event_director.gd  event_instance.gd  storyline.gd  role_binder.gd
        │   ├── world/               world_event_system.gd
        │   ├── career/              career_host.gd  career_module.gd  career_context.gd
        │   │                        employment.gd  performance.gd  shift_session.gd
        │   └── work/                reusable gameplay kernels (§9.4):
        │                            case_file/  interview/  inference/  shift_clock/  org/
        ├── careers/
        │   ├── index.json           explicit list of installed career modules
        │   └── psychiatry/
        │       ├── career.json      manifest
        │       ├── module.gd        extends CareerModule
        │       ├── sim/             patient_case.gd  patient_generator.gd  consultation.gd
        │       │                    progression.gd  hospital.gd  supervision.gd  …
        │       ├── data/            conditions.json  findings.json  questions.json
        │       │                    treatments.json  hospital_events.json  rooms.json  …
        │       ├── ui/              workspace scenes
        │       └── tests/
        ├── data/
        │   ├── events/*.json  storylines/*.json  npc_actions/*.json
        │   ├── people/              names, traits, appearance parts, goals
        │   ├── education/           stages, programs, institutions
        │   ├── economy/             tax, housing, costs, market
        │   └── schemas/             one schema per content type
        ├── ui/
        │   ├── theme/               theme.tres, tokens.gd, fonts/, icons/ (SVG)
        │   ├── kit/                 reusable components
        │   └── screens/             main_menu/ creation/ dashboard/ timeline/ people/
        │                            family_tree/ education/ career/ finance/ event/ settings/
        ├── locale/                  strings.en.csv  strings.es.csv
        └── tests/
            ├── runner/              test_runner.tscn  test_case.gd
            ├── unit/  content/  save/  soak/  ui_smoke/
            └── bots/                scripted players used by soak and balance tests
```

`careers/index.json` is an explicit registry instead of a directory scan on purpose:
directory listing of `res://` in exported builds has historically behaved differently
from the editor, and a registry is trivially verifiable (a test asserts every folder
under `careers/` is listed and vice versa).

---

## 7. Data models

All runtime models are typed `RefCounted` classes with `to_dict()` / `static
from_dict()`. IDs are short stable strings (`p_000123`, `rel_…`, `mem_…`); references
between models are **always by ID**, never by object reference, so the object graph
serializes trivially and nothing dangles silently (a test walks every ID reference).

### 7.1 Time

- Calendar: 12 months × 28 days = **336-day year**, 7-day weeks. Every month is
  exactly four weeks, so daily/weekly/monthly/yearly cadences nest without drift and
  shift rotas repeat cleanly. `GameDate` is an `int` day ordinal plus helpers.
- The player presses **Continue**. Time advances day by day until the next
  *interrupt*: a blocking event, an agenda item needing a decision (exam, appointment,
  shift the player chose to play), or the stride limit (week / month / year, user
  selectable; childhood defaults to year).
- Only systems whose cadence boundary is crossed run. Daily work is restricted to
  cheap subscribers (active professional cases, agenda), so skipping a year costs
  336 light iterations + 48 weekly + 12 monthly + 1 yearly pass.
- A **weekly time budget** (hours left after sleep, school/work, commuting) is
  allocated across activities (study, exercise, family, friends, dating, hobbies,
  side projects) through a persistent plan the player edits only when they want to.
  It is what makes life choices trade off against each other and against a career.

### 7.2 Person

One class for everyone — the player's character, their mother, a patient, a rival.
"The player" is `world.controlled_person_id`; generational continuation is changing
that ID to an heir in the same world.

```jsonc
{
  "id": "p_000123",
  "name": {"given": "Mara", "family": "Okafor", "birth_family": "Okafor"},
  "sex": "f", "gender": "woman",
  "born": 10472, "died": null, "death_cause": null,
  "appearance": {"skin": 3, "hair": "curly_long", "hair_color": 2, "eyes": 1, "build": 2, "features": [...]},
  "personality": {"openness": 0.71, "conscientiousness": 0.44, "extraversion": 0.63,
                  "agreeableness": 0.30, "stability": 0.52},
  "traits": ["ambitious", "jealous"],              // discrete, data-defined
  "attributes": {"health": 82, "happiness": 61, "intellect": 74, "looks": 58,
                 "fitness": 49, "stress": 35},      // fictional 0–100 simulation values
  "skills": {"empathy": 22, "science": 40},
  "preferences": {"likes": ["music", "hiking"], "dislikes": ["dishonesty"]},
  "goals": [{"type": "career_rank", "target": "psychiatry:attending", "priority": 0.8, "progress": 0.3}],
  "emotions": [{"type": "resentment", "toward": "p_000001", "intensity": 0.6,
                "cause": "mem_0042", "until": 11210}],
  "family": {"parents": ["p_000050", "p_000051"], "children": [], "partners": [...]},
  "household": "hh_0007",
  "education": {...}, "occupation": {...},          // summaries; details live in their systems
  "wealth_tier": 3,                                 // NPCs: coarse. Controlled person: full ledger in economy
  "lod": "A", "flags": {...}
}
```

Strengths and weaknesses are not a separate field: they are the combination of
personality, traits, attributes and skills, which is what rules actually read.

### 7.3 Relationships and memories

A `Relationship` exists per pair of people who know each other:

```jsonc
{
  "id": "rel_p000001_p000123",
  "a": "p_000001", "b": "p_000123",
  "kinds": ["friend", "colleague"],        // family:mother, romantic:dating, spouse, ex, rival, patient_of, mentor…
  "a_to_b": {"affection": 44, "trust": 30, "respect": 55, "attraction": 0},
  "b_to_a": {"affection": 38, "trust": 12, "respect": 60, "attraction": 20},
  "familiarity": 0.7, "tension": 0.4,
  "met": 9100, "last_contact": 11180,
  "modifiers": [{"axis": "trust", "dir": "b_to_a", "amount": -25, "memory": "mem_0042", "decays_to": -8, "half_life": 672}]
}
```

A `Memory` is the persistent record of something that happened:

```jsonc
{
  "id": "mem_0042", "date": 11102, "tag": "betrayal.broke_confidence",
  "roles": {"actor": "p_000001", "target": "p_000123"},
  "valence": -0.8, "intensity": 0.9, "salience": 0.85,
  "source": {"event": "uni_secret_shared", "choice": "tell_others"},
  "text": "mem.broke_confidence", "known_by": ["p_000001", "p_000123", "p_000090"]
}
```

Key rule: **opinion values are derived from a slow-moving base plus memory-linked
modifiers that decay** toward a residue. Consequences therefore persist for a
reason the game can show ("Mara distrusts you: you shared her secret (−25, fading)"),
and conditions can ask about history directly (`memory.has`) instead of only reading
a number. `known_by` drives gossip and reputation: witnesses pass memories on through
their own relationships with a probability shaped by severity and their personality,
and per-community reputation (school, workplace, profession, neighbourhood) is
computed from what that community knows.

### 7.4 NPC simulation and level of detail

| Tier | Who | Simulated | Budget |
|---|---|---|---|
| **A** | Household, close family, partners, close friends, key colleagues, active patients/clients, rivals | Monthly: emotions, goals, utility-chosen actions, full relationship updates | ≤ ~150 |
| **B** | Extended family, acquaintances, former contacts, staff | Yearly: coarse life progression (job, moves, marriage, children, health, death) | ≤ ~3,000 |
| **C** | Everyone else | Not stored. Generated on demand from seeded generators, then promoted. | unbounded |

NPC behaviour is **utility-based and data-driven**: `data/npc_actions/*.json` defines
actions (reach out, ask a favour, confront, propose, sabotage, apologise, drift away,
change job…) each with conditions, a utility expression weighted by personality,
goals, emotions and memories, and effects. Actions aimed at the controlled person
become events through the `EventDirector`, so the player experiences NPC initiative
through the same event UI. Promotion/demotion between tiers preserves identity; a
person referenced by any memory or record is never deleted, only compacted.

### 7.5 Education, economy, career (summaries)

- **Education**: `Institution` (quality, cost, selectivity), `Enrolment` (programme,
  term, courses, grades, attendance, standing), `Qualification` (degree / licence /
  certificate with grade). Grades come from intellect, allocated study hours,
  attendance, teacher relationship, stress and event outcomes. Exams are agenda
  interrupts with preparation decisions. University admission scores applications
  against programme selectivity; tuition, scholarships and student loans go through
  the economy. Career manifests name the qualifications they require, which is how
  degrees unlock careers.
- **Economy**: accounts (checking, savings, retirement, brokerage), an append-only
  `Ledger` of categorised transactions (older months are summarised), recurring items
  (salary, rent, mortgage, loan payments, child costs), loans with amortisation and
  credit score, progressive tax with withholding and an annual settlement, property
  with a regional price index, investments driven by a market model with cycles
  shared with the job market, inheritance on death, retirement income. All monetary
  values are **integer minor units**. The setting is a fictional country so tax, law
  and healthcare rules are the game's own and never claim to describe a real place.
- **Career**: `Employment` (employer institution, career id, rank, specialization,
  salary, schedule, start date), `PerformanceRecord` (per-period KPIs), professional
  reputation, licences, disciplinary record. Profession-specific state lives inside
  the career module's own save section (§9).

---

## 8. Event and consequence architecture

### 8.1 Two small languages

Everything data-driven is built from two registries, both namespaced and extensible
by systems and career modules at registration time:

- **Conditions** — a JSON tree of `all` / `any` / `not` over predicates:
  `age.between`, `stage.is`, `trait.has`, `attr.gte`, `flag.has`, `money.gte`,
  `edu.enrolled_in`, `career.is`, `career.rank_gte`, `rel.kind`, `rel.axis_gte`,
  `memory.has`, `history.chose`, `storyline.state_is`, `world.is`, `date.month_is`, …
- **Effects** — an ordered list of ops: `attr.add`, `skill.add`, `money.add`,
  `flag.set`, `rel.add`, `rel.set_kind`, `memory.add`, `emotion.add`,
  `event.schedule`, `storyline.start`, `storyline.goto`, `edu.grade_modifier`,
  `career.reputation_add`, `person.spawn`, `person.bind`, …

The same two registries are used by events, storylines, NPC actions, interaction
menus and career outcomes. There is exactly one implementation of "can this happen?"
and one of "make this happen", which is what prevents duplicate systems.

### 8.2 Event definitions

```jsonc
{
  "id": "uni.study_group_invite",
  "tags": ["university", "social"],
  "trigger": {"type": "pulse", "cadence": "monthly"},   // or on_action / scheduled / storyline
  "conditions": {"all": [{"edu.enrolled_in": {"level": "university"}}, {"not": {"flag.has": "uni.met_study_partner"}}]},
  "roles": {
    "peer": {"from": "classmates", "where": {"not": {"rel.kind": "enemy"}},
             "prefer": "personality_compatible", "or_spawn": "university_student"}
  },
  "weight": {"base": 10, "modifiers": [{"if": {"trait.has": "outgoing"}, "mul": 1.5}]},
  "limits": {"max_times": 1, "cooldown_days": 0},
  "text": {"title": "ev.uni.study_group.title", "body": "ev.uni.study_group.body"},
  "choices": [
    {"id": "join", "text": "…",
     "outcomes": [{"weight": 1, "effects": [
        {"rel.add": {"with": "$peer", "kind": "acquaintance", "affection": 12}},
        {"memory.add": {"tag": "social.studied_together", "roles": {"actor": "$player", "target": "$peer"}}},
        {"storyline.start": {"id": "uni_connection", "bind": {"other": "$peer"}}},
        {"flag.set": "uni.met_study_partner"}]}]},
    {"id": "decline", "text": "…", "outcomes": [ … ]}
  ]
}
```

- **Roles** bind named slots to real people by query. An event cannot fire unless its
  required roles bind; bindings are stored with the event instance, with scheduled
  follow-ups, and with storylines, so "the person you met in 2nd year" stays that
  person forever.
- **Choices** may carry visibility/enabled conditions (shown disabled with the unmet
  requirement), a **check** (probability from named stats/skills, shown to the player
  as a qualitative odds band), and weighted **outcomes** each with conditions,
  effects and result text.
- Every fired event and chosen option is appended to `events.history`, queryable by
  `history.chose`. This is the world's long-term memory of decisions.

### 8.3 Storylines (event chains)

A storyline is a small persistent state machine with bound roles and variables:

```
uni_connection(other):
  acquainted ──(affection≥50)──▶ friends ──(attraction, both single)──▶ dating ──▶ …
      │                             │ (betrayal memory)                     │ (breakup)
      │ (no contact 2y)             ▼                                       ▼
      └────────▶ lost_contact     rivals ◀────────────────────────────── exes
```

States declare: entry effects, events enabled while in the state, transitions
(condition- or event-driven), and *long-fuse hooks* — e.g. while `other` works in
the player's profession, the job market consults the storyline: a `friends` state
adds a referral opportunity, a `rivals` state adds a blocked application or a hostile
interview panel member; `lost_contact` enables a reunion event when circumstances
bring them back into proximity (same employer, same town, a wedding, a hospital
admission). The instance is saved with its bindings, so the consequence can land
decades later without any special-case code.

### 8.4 The Director

Selection each cadence step, in priority order:

1. **Due scheduled events** (deterministic consequences of earlier choices).
2. **`on_action` hooks** (graduation, promotion, shift end, relationship status
   change, birth, death, move, bankruptcy …).
3. **Storyline-enabled events** whose conditions hold.
4. **Pulse pool**: eligible events drawn by weight from buckets pre-indexed by life
   stage and tag. Weights are multiplied by *relevance*: bindings to people with
   strong relationships or salient memories, links to active goals, and recent
   topics. Unconnected filler is possible but systematically out-competed.

A pacing budget limits blocking interrupts per period and spaces heavy events;
non-blocking outcomes go to the timeline/inbox instead of a modal. Cooldowns,
`max_times` and mutual-exclusion groups prevent repetition.

### 8.5 Content safety net

Run in the test suite on every change:

- JSON schema validation for every content type.
- Reference linting: unknown event/storyline/role/op/predicate/locale key, storyline
  states that are unreachable or have no exit, choices with no outcomes, effects
  referencing unbound roles.
- A **fuzz player** that fires every event under generated worlds satisfying its
  conditions and takes every choice, asserting no script errors and no invariant
  violations.
- An in-game debug console (dev builds) to trigger events, inspect why an event is
  or is not eligible, and view storyline instances.

---

## 9. Career plugin architecture

### 9.1 Split of responsibilities

| `CareerHost` (core, generic, written once) | A career module (plugin, per profession) |
|---|---|
| Job market, applications, interviews, offers | What a working day *is*: workspace, tasks, tools |
| Employment contract, rank ladder, pay, schedule, leave | Profession-specific persistent state (cases, clients, projects) |
| Qualification / licence checks from the manifest | Domain rules, hidden truth, outcomes |
| Period performance reviews → promotion, bonus, warning, dismissal | KPIs it reports for each period |
| Professional reputation, disciplinary process | Profession-specific events, NPC roles and storylines |
| Retirement, pension, career change | Specialization branches |
| Calling modules at the right times; saving their state | Its own save format version and migrations |

### 9.2 Manifest (`careers/<id>/career.json`)

```jsonc
{
  "id": "psychiatry", "category": "medicine", "save_version": 1,
  "module_script": "res://careers/psychiatry/module.gd",
  "workspace_scene": "res://careers/psychiatry/ui/workspace.tscn",
  "entry": {"qualifications": ["degree.medicine", "licence.medical"], "min_age": 24},
  "ranks": [
    {"id": "trainee",   "salary": 4200000, "promotion": {"min_months": 24, "kpi": {"quality": 0.60}, "requires": ["exam.psych_part1"]}},
    {"id": "resident",  "salary": 5800000, "promotion": {"min_months": 36, "kpi": {"quality": 0.68}, "requires": ["exam.psych_board"]}},
    {"id": "attending", "salary": 12500000, "promotion": {…}},
    {"id": "senior_specialist", …}, {"id": "department_director", …}, {"id": "hospital_administrator", …}
  ],
  "specializations": [{"id": "adult"}, {"id": "child_adolescent", "from_rank": "resident"},
                      {"id": "forensic", …}, {"id": "geriatric", …}],
  "schedules": {"trainee": {"pattern": "weekdays", "hours": [8, 17], "on_call_per_month": 2}, …},
  "content": {"events": ["data/hospital_events.json"], "locale": ["locale/psychiatry.en.csv"]},
  "expenses": [{"id": "licence_fee", "cadence": "yearly", "amount": 60000}]
}
```

### 9.3 The module contract (`core/career/career_module.gd`)

```gdscript
class_name CareerModule extends RefCounted

# --- lifecycle -----------------------------------------------------------
func register(ctx: CareerContext) -> void            # add effect ops, predicates, events, NPC roles
func on_hired(person_id: String, employment: Employment) -> void
func on_rank_changed(old_rank: String, new_rank: String) -> void
func on_left(reason: String) -> void

# --- time ----------------------------------------------------------------
func on_days_advanced(from: int, to: int) -> void     # progress persistent cases between shifts
func get_agenda(from: int, to: int) -> Array[AgendaItem]   # shifts, appointments, deadlines

# --- play ----------------------------------------------------------------
func begin_shift(spec: ShiftSpec) -> ShiftSession     # interactive session (plain serializable data)
func auto_resolve_shift(spec: ShiftSpec, policy: Dictionary) -> ShiftReport
func evaluate_period(from: int, to: int) -> PerformanceReport

# --- presentation --------------------------------------------------------
func get_dashboard() -> Dictionary                    # summary for the career dashboard

# --- persistence ---------------------------------------------------------
func to_dict() -> Dictionary
func from_dict(data: Dictionary) -> void
func migrate(data: Dictionary, from_version: int) -> Dictionary
```

`CareerContext` is the *only* door a module has into the world: read-only queries,
`execute_effects()`, person generation/binding, RNG stream `career.<id>`, clock,
content access, and event scheduling. A module cannot reach into another system's
state directly, which keeps modules independently testable and removable.

Two rules make "no fake functionality" structural rather than aspirational:

- **`auto_resolve_shift` runs the same simulation as an interactive shift**, driven
  by a policy bot whose decision quality comes from the character's skills. There is
  no second, cheaper model that awards money. Shifts the player does not play still
  produce real patients, real notes, real outcomes and real mistakes.
- **A `ShiftSession` is plain data**, so it can be saved mid-shift and resumed exactly
  (§11), and tests can drive it without any UI.

`PerformanceReport` uses a host-defined vocabulary (`quality`, `productivity`,
`conduct`, `safety_incidents`, `complaints`, `commendations`, plus free-form module
detail), so promotion, bonus and dismissal logic is written once in `CareerHost`.

### 9.4 Reusable gameplay kernels (`core/work/`)

Thirty careers are only tractable if they compose a small number of deep, tested
kernels. Each kernel is built when the first career needs it — never speculatively.

| Kernel | What it models | Built in | First user | Later users |
|---|---|---|---|---|
| `case_file` | Persistent case with hidden truth, discovered findings (with source, date, reliability), documents, decisions, outcome | M5 | Psychiatry | All medicine, law, detective, forensics, analyst |
| `interview` | Question bank, approach/tone, subject disposition (rapport, guardedness), disclosure and distortion | M5 | Psychiatry | Police interview, cross-examination, GP, teacher–parent, journalist-style careers |
| `inference` | Findings ↔ hypotheses likelihood model, differential ranking, evidence sufficiency | M5 | Psychiatry | Diagnosis in all medicine, detective deduction, forensic analysis, financial analysis |
| `shift_clock` | Shift time, action costs, task queue, triage/prioritisation, interruptions | M5 | Psychiatry | ER, police patrol, court docket, class timetable |
| `org` | Staff rota, budget, policy decisions, inspections, morale | M5 (lite) → M6 | Dept. director / administrator | CEO, school administrator, entrepreneur |
| `argument` | Claims, evidence admissibility, persuasion of a decider | later | Law | Prosecutor, judge, corporate negotiation |
| `project` | Brief → multi-stage work with quality axes, deadline, client satisfaction | later | A creative career | Designer, photographer, producer, researcher, entrepreneur |
| `lesson` | Group of learners with individual states, plan → deliver → assess | later | Teacher | Professor, school administrator |

Planned mapping (design intent, **not implemented**): each future career = kernels +
at least one mechanic that is uniquely its own.

| Career group | Kernels | Unique mechanic (examples) |
|---|---|---|
| GP, pediatrician, neurologist, emergency physician, nurse | case_file, interview, inference, shift_clock | Physical exam & test ordering; ER triage under load; nursing task rounds and escalation |
| Surgeon | case_file, shift_clock | Operative planning and step-wise procedure decisions with complication management |
| Defense lawyer, prosecutor, corporate lawyer, judge | case_file, interview, argument | Trial phases; plea/charge decisions; sentencing within fictional statute; contract risk review |
| Police officer, detective, forensic investigator, criminal analyst | case_file, interview, inference, shift_clock | Scene processing; lead board; lab queue and chain of custody; pattern linkage across cases |
| Teacher, professor, school administrator, researcher | lesson, project, org | Classroom management; grant → study → publication pipeline |
| Entrepreneur, CEO, financial analyst, real-estate investor | org, project, inference | Company model with market; valuation calls; property deal pipeline |
| Fashion / interior designer, makeup artist, photographer, actor, music producer | project | Design/composition editor; shoot planning; audition and role preparation; track arrangement |

---

## 10. Module interface summary

| Module | Reads | Writes (only via) | Emits | Provides |
|---|---|---|---|---|
| Time | — | `clock`, `agenda` | `date_advanced`, `interrupt` | cadence dispatch, scheduling |
| People | `clock` | `people` | `person_born/died/stage_changed` | generation, aging |
| Family | `people` | `families`, `households` | `married/divorced/birth/succession` | kinship queries |
| Social | `people` | `relationships`, `memories` | `relationship_changed`, `memory_added` | `rel.*`, `memory.*` ops & predicates |
| NPC | `people`, `relationships` | effects only | `npc_action` | agent tick |
| Education | `people`, `economy` | `education` | `enrolled/graduated/exam_result` | `edu.*` |
| Economy | `clock`, `careers` | `economy` | `transaction`, `debt_default` | `money.*`, ledger queries |
| CareerHost | `education`, `people` | `careers` | `hired/promoted/dismissed/shift_ended` | module hosting, `career.*` |
| Events | everything (read-only) | `events` + effects | `event_presented/resolved` | director, storylines |
| Save | `Simulation.to_dict()` | files | `saved/loaded/save_failed` | slots, migration |
| UI | queries, signals | commands | — | — |

---

## 11. Save system and world persistence

### 11.1 Guarantees

1. Closing the game at any point — including mid-shift, mid-consultation or with an
   event dialog open — and reloading resumes **exactly** that state.
2. A failed or interrupted write never destroys the previous save.
3. A save from an older game version loads through migrations or is refused with a
   clear message; it is never loaded half-understood.
4. Save → load → continue produces the same future as never having saved (given the
   same inputs).

### 11.2 Layout

```
user://saves/<slot_id>/
  meta.json          small, uncompressed: character name, age, date, career, playtime,
                     format_version, game_version  (drives the load menu without loading worlds)
  world.sav          ZSTD-compressed JSON: the full Simulation.to_dict()
  world.sav.bak1..3  rolling previous versions
user://settings.cfg  (ConfigFile; not part of a save slot)
```

### 11.3 Document shape

```jsonc
{
  "format_version": 1, "game_version": "0.2.0", "checksum": "sha256 of sections",
  "sections": {
    "clock": {...}, "agenda": [...], "people": {...}, "families": {...}, "households": {...},
    "relationships": {...}, "memories": {...}, "education": {...}, "economy": {...},
    "events": {"flags": {...}, "history": [...], "scheduled": [...], "storylines": [...], "pending": {...}},
    "world_context": {...},
    "careers": {"employment": {...}, "modules": {"psychiatry": {"version": 1, "data": {...}}}},
    "session": {"active_shift": {...}, "ui_resume": {"screen": "career.workspace", "args": {...}}},
    "rng": {"world": {"seed": "…", "state": "…"}, "events": {...}, "npc": {...}, "career.psychiatry": {...}}
  }
}
```

### 11.4 Rules (each from a verified pitfall or guarantee)

- **Typed deserialization.** Because JSON yields floats, every model's `from_dict`
  casts explicitly; a round-trip test per model asserts `to_dict(from_dict(x)) == x`
  including value *types*.
- **64-bit values as strings** (RNG seed/state). Money stays within exact-float
  integer range and is validated on load.
- **Atomic write**: serialize → write `world.sav.tmp` → reopen and verify checksum →
  rotate backups → `rename`. Load falls back to the newest valid backup and tells
  the player.
- **Migrations**: `core/save/migrations/v001_to_v002.gd …` transform raw dictionaries
  before deserialization; each career module migrates its own section. A golden save
  from every released format version is kept in `tests/save/fixtures/` and must load.
- **Named RNG streams** (`world`, `events`, `npc`, `career.<id>`, `cosmetic`): adding
  content consumed by one stream does not shift outcomes in the others.
- **Autosave** after time advances, at shift end, every N shift actions, and on
  window-close request. Manual slots are separate from the autosave slot.
- Save files are data only. Nothing in a save is ever executed.

### 11.5 What is persisted

Character data, every instantiated NPC, relationships and memories, education and
qualifications, full financial state and ledger, employment and performance history,
career-module state (for psychiatry: every patient, chart, note, decision, outcome),
event flags/history/scheduled events/storyline instances, family generations and
succession history, world context, clock, agenda, RNG streams, and the active
session (open shift and where the UI was).

### 11.6 Growth control

History and ledger are append-only but compacted: old ledger months collapse into
category totals; closed cases keep their summary and decisive records while routine
notes are condensed; Tier-B people drop derived caches. Target: < 5 MB compressed
after a 90-year life with a full career. A soak test tracks this number. If it is
exceeded, the fallback is splitting sections into separately loaded files — the
section structure above is designed so that this needs no model changes.

---

## 12. UI architecture

### 12.1 Structure

- **Router** (autoload): a screen stack with animated transitions; screens are
  scenes under `ui/screens/` and career workspaces. It restores the saved `ui_resume`.
- **Screens** are thin: build from `Queries`, send `Commands`, refresh on `SimBus`
  signals. No game rules in view scripts (enforced by review and by the layer test).
- **UI kit** (`ui/kit/`): Card, StatBar, Badge, Avatar, ListRow, TabBar, Modal,
  Toast, Tooltip/Explainer, Timeline item, Tree node (family tree), simple charts
  drawn with `_draw()` (net worth, grades, patient symptom trends), Agenda item.
- **Theme**: one `Theme` resource generated from design tokens (palette, type scale,
  spacing, radii, motion durations) so the look is coherent and themable
  (default, high-contrast).

### 12.2 Screens

Structure follows the owner's reference (identity strip, life log, one primary
time-advance action, domain navigation, wellbeing meters); the visual identity is
original. Both are specified in `UI_DIRECTION.md`.

Main menu / slots · Character creation · **Dashboard** (status, agenda, Continue) ·
Life timeline · People list & character profile · NPC interaction · Family tree ·
Education · Career dashboard · **Professional workspace** (module-owned) · Finance
(accounts, ledger, loans, property, investments, tax) · Event dialog · Inbox ·
Settings & accessibility.

### 12.3 Visual assets without an art team

- Icons: an in-repo SVG set (Godot imports SVG natively), consistent stroke/grid.
- Portraits: procedural, layered vector parts driven by `appearance` data, aged by
  life stage, with expression variants driven by mood — every NPC has a persistent
  recognisable face without per-character art.
- Hospital and other places: stylised 2D floor plans/room scenes built from vector
  parts.

This is an honest constraint: the target is a clean, coherent, professional
interface, not hand-painted illustration.

### 12.4 Responsiveness and accessibility

- **Portrait-first** (see [`UI_DIRECTION.md`](UI_DIRECTION.md)): base 720×1280,
  `canvas_items` stretch, `expand` aspect; container-based layouts; the same
  components re-flow into a multi-column layout above a width breakpoint
  (desktop, tablet landscape). Both layouts are covered by the UI smoke test.
- UI scale and font size settings; high-contrast theme; colour-blind-safe palette
  with **no colour-only signals** (icon/shape/text always accompany colour);
  reduce-motion toggle; full keyboard/gamepad focus navigation; accessible names on
  controls for screen readers (API present in 4.7.2 — actual screen-reader behaviour
  still needs testing on a real desktop, which this container cannot do).
- Content settings for sensitive themes (§13).

### 12.5 Optional 3D seam

A workspace may embed a `SubViewportContainer` showing a 3D scene (e.g. a hospital
corridor or consulting room) that *presents* the same simulation state the 2D
interface drives. 3D never owns rules. This is deliberately deferred: it will only
be built if, at Milestone 7, the 2D experience is complete and Blender-authored
assets can be produced at a quality that adds rather than subtracts. The tooling
is no longer the obstacle (Blender is installed and the export/import path is
verified); asset quality and scope are.

---

## 13. Sensitive content policy

The game simulates illness, death, crime, family conflict and psychiatric care.

- All clinical, legal and financial content is **fiction with internally consistent
  rules**. Conditions are simulation profiles, treatments are abstract classes with
  abstract intensity levels (no real drug names, doses or protocols), and legal
  mechanisms (e.g. an involuntary "safety hold") are explicitly the fictional
  country's rules. A persistent notice says the game is not medical or legal guidance.
- Risk and self-harm are handled as professional assessment decisions, described
  non-graphically; no method detail. Child patients are handled with the same care.
- Patients are written as people with histories and dignity, not as hazards or jokes.
- A content setting can reduce or exclude the most sensitive themes; the event
  director honours it through content tags.

---

## 14. Dependency policy

- **Zero third-party code by default.** Engine + in-repo GDScript only. Any future
  addon needs: a written justification in this document, a pinned version, a licence
  check, and a verification test.
- External tools used only at development time: pinned Godot, pinned Blender
  (asset authoring only), Python (optional linting), xvfb (screenshots).
- No network access at runtime. The game is fully offline.

---

## 15. Engineering standards

- Static typing everywhere; `untyped_declaration` and the `unsafe_*` family treated
  as errors in project settings.
- One class per file, `class_name` for models and systems, files ≲ 300 lines; a
  growing file is a signal to split responsibilities, not to add regions.
- Signals up, calls down; no `get_node("/root/…")` reach-arounds; no singletons in
  `core/`.
- Every bug fix lands with a test that failed before it.
- No silent fallbacks: missing content, unknown ops and failed loads are errors that
  surface in tests and logs.
- Player-facing text only through locale keys.

### Automated tests

| Suite | What it proves |
|---|---|
| Unit | Each system's rules (aging, opinion maths, grades, loan amortisation, tax, promotion logic, date maths). |
| Content | Schemas, references, storyline reachability, locale coverage (§8.5). |
| Save | Per-model typed round-trip; full-world round-trip; atomic write/backup recovery; migrations on golden saves; **determinism**: `advance(n)` ≡ `save → load → advance(n)` by world hash. |
| Soak | A bot plays hundreds of full lives headless with random and scripted policies: no errors, invariants hold (ledger balances, no dangling IDs, ages consistent, one employment at a time, save size budget). |
| Career | Module contract conformance for every installed career; psychiatry-specific solvability and balance tests (see `PSYCHIATRY_DESIGN.md` §10). |
| Layering | `core/` has no forbidden references. |
| UI smoke | Every screen instantiates under xvfb with a populated world; **every enabled `Button` has a connected handler** (mechanical guard against fake buttons); focus traversal reaches all controls; screenshots are captured for review. |

`tools/run_tests.sh` runs everything headless and returns a process exit code.

---

## 16. Technical risks

| # | Risk | Severity | Mitigation |
|---|---|---|---|
| 1 | **Scope.** The full vision (≈30 careers each with dedicated mechanics) is studio-scale work. | Critical | Vertical slices; kernels (§9.4); one deep career before breadth; honest status reporting; "playable over feature count" at every milestone. |
| 2 | Two time scales (decades of life vs. minutes of a shift) in one calendar. | High | Single day-ordinal clock; shifts are sessions inside a day; auto-resolve uses the same sim; persistent cases progress via `on_days_advanced`. Prototype this interaction first in Milestone 4. |
| 3 | Hidden-truth clinical sim feels like guessing, or is trivially solvable. | High | Likelihood-matrix content with a linter; solver-bot tests (thorough play must beat careless play; correct treatment must beat wrong treatment; every generated case must be solvable from obtainable evidence). |
| 4 | Event content becomes disconnected or repetitive despite the architecture. | High | Role binding + storylines + relevance weighting; content lint; fuzz player; repetition metrics in soak tests. Quality here is mostly *writing volume*, which is the largest content cost. |
| 5 | Save compatibility and size over long lives. | Medium | Versioned migrations with golden fixtures from the first release; compaction; size tracked by soak test. |
| 6 | NPC LOD causes inconsistencies (a Tier-B friend's life contradicts shared history). | Medium | Promotion re-derives from stored facts, never regenerates; identity and memories are tier-independent. |
| 7 | Engine/API drift: 4.7.2 is newer than most reference material. | Medium | Verify against the pinned engine; pin version; upgrade only behind a green test suite. |
| 8 | UI quality without artists; "commercial quality" visuals. | Medium | Design tokens, procedural portraits, vector art, motion polish; honest limits stated in §12.3. |
| 9 | Things this container cannot verify: audio, real GPU rendering, touch input, screen readers, non-Linux builds. | Medium | Listed in `KNOWN_ISSUES.md`; require owner playtesting on target hardware. |
| 10 | Ephemeral dev container: engine not preinstalled; third-party repos blocked. | Low | `install_godot.sh` (tested from clean); zero-dependency policy. |
| 11 | Sensitive subject matter handled badly. | High (reputational) | Policy §13; content tags and settings; review of all clinical writing. |
| 12 | Export pipeline untested (templates ~1 GB; Android needs SDK + signing). | Medium | Do a trivial export smoke test early (Milestone 2) on the chosen desktop target instead of discovering problems at Milestone 8. |

---

## 17. Open decisions for the project owner

Listed with the default that will be used if no preference is given — see
`ROADMAP.md` §7.
