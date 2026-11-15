# LIFEVERSE — UI Direction

Status: **direction only.** No interface has been built. The screens are designed
and built in Milestone 2 onward; visual choices here are proposals that will be
shown as real screenshots for approval before they are treated as settled.

---

## 1. The reference and how it is used

On 2026-11-15 the project owner supplied two BitLife store screenshots as a guide,
with the instruction: use them as a guide, then make our own menus.

So the reference informs **structure and flow**. It is not a visual template.
The screenshots themselves are not stored in this repository.

### What the reference does well (patterns we learn from)

| Pattern in the reference | Why it works |
|---|---|
| Portrait, one-handed phone layout | The whole game is reachable with a thumb. |
| Identity strip at the top: portrait, name, current role, money | You always know who you are and where you stand. |
| A chronological life log grouped by age as the main content | The life *is* the story; reading back is the reward. |
| One large primary button, centred, that advances time | No doubt about what moves the game forward. |
| Four category entries around it (school/work, assets, relationships, activities) | Everything else is one tap away, grouped by life domain. |
| Persistent wellbeing bars with a percentage and colour | State is readable at a glance. |
| A stats overview at the moment of birth | The starting hand is shown before play begins. |

### What LIFEVERSE will not take from it

Name, logo, wordmark, colour scheme (red frame, yellow dotted background, rainbow
band), typography, the emoji-style head avatars, icon artwork, mascot poses,
slogans, and event wording. None of these are reused or imitated. LIFEVERSE has its
own identity (§3).

---

## 2. Where LIFEVERSE deliberately differs

These follow from the design in `ARCHITECTURE.md`, not from wanting to look different.

| Area | Reference | LIFEVERSE |
|---|---|---|
| Advancing time | Fixed one-year step | **Continue** advances to the next thing needing you; stride (week / month / year) selectable; a preview shows what it will stop at. |
| Life log | Read-only text | Every entry is interactive: names open the person's profile; an entry opens the memory it created and what it later caused. |
| People | A list with a bar | Profiles with a persistent procedural portrait, personality, shared history, and *why* they feel as they do about you. |
| Work | A menu of actions | A full **professional workspace** per career (hospital map, charts, consultations) entered from the Work tab. |
| Money | A balance | Accounts, ledger, loans, property, investments, tax, with charts. |
| Wellbeing meters | Colour-coded bars | Icon + label + value on every meter; colour is never the only signal (accessibility). |
| Agenda | — | Upcoming exams, appointments, shifts and deadlines are always visible. |
| Places and people | Static icons | Place scenes (home, hospital, street) with animated characters doing what the simulation says, facial expressions driven by emotion, day/night and weather (ARCHITECTURE §22). |
| Daily life | Menu actions | A routine you edit, a day you can open and schedule, and moments played as scenes (ARCHITECTURE §18). |
| Conversations | Single-tap interactions | Dialogue with topics that depend on shared history, a choice of approach, and visible emotional reactions (ARCHITECTURE §19). |

---

## 3. Proposed original identity (to be validated with screenshots in M2)

- **Mood:** calm, editorial, adult — closer to a well-made journal or a clinical
  dashboard than to a toy. It has to carry serious subject matter without becoming grim.
- **Surfaces:** layered cards on a quiet background; generous spacing; soft corner
  radius; subtle depth. No heavy outlines or cartoon framing.
- **Colour:** a restrained neutral base with one brand accent, plus a small set of
  semantic colours for life domains (family, education, career, money, health).
  Light and dark themes and a high-contrast theme from the same tokens.
- **Type:** one humanist sans family for interface text and a contrasting face for
  the life log, so reading the story feels different from operating the controls.
- **Portraits:** procedurally assembled from layered vector parts driven by each
  person's appearance data; they age with the person and change expression with
  mood. Not emoji-style heads.
- **Icons:** one in-repo SVG set on a shared grid and stroke weight.
- **Motion:** short, purposeful transitions (card rise, meter change, time
  advancing); all removable with the reduce-motion setting.

Exact palette, fonts and icon style are decided when the first screens exist and can
be judged on screen, not in a document.

---

## 4. Layout

**Portrait-first.** The reference is a phone-portrait game, so the primary layout is
portrait and thumb-reachable. The same components re-flow into a multi-column layout
on wide windows (desktop), where the life log, the current screen and the agenda can
sit side by side.

Home screen structure (wireframe of arrangement only, not of appearance):

```
┌────────────────────────────────────┐
│ [portrait]  Name                   │  identity: who, life stage · age,
│             Role / stage · age     │  role, date, money, agenda count
│  balance                 date  (2) │
├────────────────────────────────────┤
│  Year · Age                        │
│   ▸ entry (domain icon, people     │  life log: grouped by year, entries
│     are tappable)                  │  are interactive, newest at bottom
│   ▸ entry                          │
│  Year · Age                        │
│   ▸ entry                          │
├────────────────────────────────────┤
│  next: Exam in 3 days · Shift Mon  │  agenda preview (what Continue stops at)
├────────────────────────────────────┤
│  [meter] [meter] [meter] [meter]   │  wellbeing: icon + label + value
├────────────────────────────────────┤
│  Life   People  (CONTINUE)  Work  Money │  primary action centred; domains around it
└────────────────────────────────────┘
```

"Work" becomes "School" while the character is in education and is hidden in infancy.

Wide layout (desktop / tablet landscape):

```
┌──────────┬───────────────────────────────┬──────────────┐
│ identity │  current screen               │  agenda      │
│ meters   │  (life log, profile, finance, │  inbox       │
│ nav      │   workspace …)                │  Continue    │
└──────────┴───────────────────────────────┴──────────────┘
```

Professional workspaces (for example the hospital) get the full window in both
layouts, with a persistent shift clock and a way back to the life view.

---

## 5. Process for building screens

1. Build the screen against real simulation data (never mock data).
2. Capture screenshots in both layouts and both themes with `tools/screenshot.sh`.
3. Show them to the project owner; adjust.
4. Only then record palette/type decisions here as settled.
