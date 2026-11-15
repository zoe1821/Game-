# LIFEVERSE

An advanced life and career simulation built with Godot 4 and GDScript: live a whole
life, and actually *do* your profession — starting with a deep psychiatry career.

**Status: Milestone 1 (research and architecture) complete, awaiting review.
There is no playable game yet.** See [`PROJECT_STATUS.md`](PROJECT_STATUS.md).

## Documents

| Document | Contents |
|---|---|
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | Environment findings, technology decisions, layers, directory structure, data models, event/consequence engine, career plugin architecture, save system, UI, testing, risks |
| [`docs/PSYCHIATRY_DESIGN.md`](docs/PSYCHIATRY_DESIGN.md) | Design of the first deep career module |
| [`docs/UI_DIRECTION.md`](docs/UI_DIRECTION.md) | Interface reference, what is and is not taken from it, original visual direction, layouts |
| [`docs/ROADMAP.md`](docs/ROADMAP.md) | Milestones, acceptance criteria, workload estimate, open decisions |
| [`docs/DEVLOG.md`](docs/DEVLOG.md) | Development log |
| [`docs/KNOWN_ISSUES.md`](docs/KNOWN_ISSUES.md) | Known bugs, unverified items, unresolved tasks |

## Engine

Godot **4.7.2 stable**, pinned. On Linux x86_64:

```bash
lifeverse/tools/install_godot.sh     # downloads, checksum-verifies, links `godot`
```

On Windows/macOS, download the same version from <https://godotengine.org/download/archive/>.

Optional, only for authoring 3D assets — Blender **5.3.0**, pinned:

```bash
lifeverse/tools/install_blender.sh   # ~400 MB download, checksum-verified, links `blender`
```

The Godot project will live in `lifeverse/game/` from Milestone 2.

## Relationship to the rest of this repository

The repository root contains an earlier, separate Unity prototype
("Psychiatric Hospital Simulator"). LIFEVERSE does not modify or depend on it; see
`docs/ARCHITECTURE.md` §3.
