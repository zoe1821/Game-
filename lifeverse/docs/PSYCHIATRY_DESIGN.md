# LIFEVERSE — Psychiatry Career Module: Design

Status: **design, awaiting review** (Milestone 1). Nothing here is implemented.
Implementation is Milestone 5; it depends on the career framework of Milestone 4.

> **Fiction notice.** Every condition, treatment, rule and outcome in this module is
> a game simulation with invented, internally consistent rules. It is not clinical
> or legal information and must never be presented as such. Treatments are abstract
> classes with abstract intensity levels; there are no real drug names, doses or
> protocols anywhere in the game. This notice also appears in-game.

Carried over from the repository's earlier Unity design (`DESIGN.md`): the hidden
patient model (§5, §20), strict separation of symptoms / observations / history /
tests / diagnosis / treatment / evolution (§27), "the diagnosis is never shown
automatically" (§9), delayed and imperfect treatment response (§12), and correctable
errors (§21). Dropped: owning and building the hospital — in LIFEVERSE the player is
an employee until the top two ranks, where management arrives as a career stage.

---

## 1. The experience we are building

You are Dr. *You*, a trainee at Saint Brannoch Psychiatric Hospital. It is 08:00.
The night team hands over two inpatients: one slept, one did not. Your clinic list
has a new referral — a 34-year-old sent by a family doctor for "low mood, not
coping" — and two follow-ups. You open the referral letter, notice the previous
record mentions a period of unusually high energy three years ago that nobody
followed up, and decide to ask about it. The patient is guarded; a blunt question
closes them down, so you change approach. Forty minutes of shift time later you have
a picture, a differential with two live hypotheses, and a decision to make about
which one to treat first and how soon to see them again. Your supervisor reads your
note that evening and asks why you did not contact the patient's sister.

Three weeks later the patient returns — better, worse, or not at all — because of
what you decided. Their sister remembers whether you called.

The core loop is **gather → interpret → decide → document → live with it**, under a
clock, with people who remember.

---

## 2. Hospital environment

The hospital is an `Institution` in the world with a persistent staff of real
people (Tier A/B persons with personalities, goals and relationships to the player).

| Area | Gameplay role |
|---|---|
| Reception | Day's arrivals, no-shows, walk-ins; front-desk staff relationship affects scheduling favours. |
| Waiting room | Visible queue and wait times; behaviour can be observed before the consultation (an early source of findings). |
| Consultation offices | Outpatient assessments and follow-ups: the main interview workspace. |
| Emergency assessment area | Unscheduled, time-pressured assessments; disposition decisions; on-call shifts. |
| Inpatient units | Ward rounds, daily reviews, observation levels, leave and discharge decisions. |
| Treatment & observation rooms | Monitoring after emergencies, treatment sessions, de-escalation situations. |
| Medical records department | Request old records (arrive after a delay), find discrepancies, complete overdue documentation. |
| Staff offices | Supervision meetings, team meetings, colleague conversations, later: rota and budget work. |

Presentation: a stylised 2D floor plan. Rooms show live state (who is waiting,
which beds are occupied, alerts). Selecting a room opens its workspace. Moving
between areas costs shift time, so where you are matters when an emergency arrives.

---

## 3. Patients

A patient is a **`Person` in the world** (so they have family, a job, money
troubles, and can be met again outside the hospital) plus a `PatientCase`.

### 3.1 Hidden truth (never shown to the player)

```jsonc
{
  "condition": "sim.depressive_episode",          // primary simulation profile
  "comorbid": ["sim.alcohol_misuse"],
  "severity": 0.62,                                // 0–1
  "symptoms": {"low_mood": 0.8, "anhedonia": 0.7, "early_waking": 0.6, "guilt": 0.4, "poor_concentration": 0.5},
  "history_facts": ["past_elevated_episode_3y", "father_similar_illness", "job_loss_2m"],
  "risk": {"level": 0.35, "drivers": ["hopelessness"], "protective": ["children", "sister_support"]},
  "insight": 0.5, "adherence": 0.6,
  "disclosure": {"guardedness": 0.6, "minimises": ["alcohol"], "exaggerates": [], "topic_guard": {"safety": 0.7}},
  "response": {"tx.talking_structured": 0.6, "tx.med_mood_lifting": 0.7, "tx.med_stabilising": 0.2},
  "trajectory": "episodic", "stressors": [...], "triggers": [...]
}
```

Generation is seeded and constrained: a condition profile (data) defines which
symptoms and history facts are likely, typical ages, courses and comorbidities; the
patient's *person* (personality, family, circumstances) shapes disclosure, adherence
and stressors. Some presentations are deliberately not what they first seem: a
physical-health mimic, substance effects, ordinary distress that needs no diagnosis,
or (in forensic work) feigned symptoms.

Planned condition profiles for the first release (about 12, names in the game are
plain descriptive labels): depressive, bipolar-type, generalised anxiety, panic,
trauma-related, obsessive-compulsive, psychotic, substance-related, neurocognitive
decline, attention/hyperactivity (child), physical-health mimic, adjustment/no
disorder.

### 3.2 The chart (what is known)

Everything the player sees is a **finding** with provenance:

```jsonc
{"id": "f_018", "code": "alcohol_use", "value": "moderate", "source": "patient_report",
 "date": 11840, "by": "p_000001", "reliability": "self_report", "note_id": "n_007"}
```

Sources: referral letter, previous records (may be incomplete or wrong), patient
report, direct observation, collateral (family, school, police), investigations,
rating scales, nursing notes. The chart can therefore contain **contradictions**
(patient says "a drink at weekends", sister says "every night"). Spotting and
resolving them is gameplay: the chart view offers a *compare* mode that lines up
findings on the same topic across sources and dates.

Chart sections: demographics & contacts · presenting complaint · psychiatric
history · medical history · family history · personal/social history · mental state
observations (per visit) · investigations · risk assessments · diagnoses (history
of working and revised) · medication/treatment history with responses and side
effects · treatment plan · progress notes · correspondence · follow-up schedule.

Documentation is a mechanic, not flavour: the player chooses which findings go in
the note and the note's conclusions. Incomplete notes lower documentation KPIs,
weaken your position in complaints and inspections, and — because colleagues and
your future self read the chart — missing information is genuinely missing later.

---

## 4. The consultation

Uses the `interview`, `inference` and `shift_clock` kernels.

### 4.1 Actions (each costs shift minutes)

| Action | Detail |
|---|---|
| Review records | Read referral, past notes, results. Reveals documented findings; flags gaps. |
| Ask | Pick a topic (presenting complaint, mood, anxiety, sleep & appetite, thinking & perception, substances, safety, past history, family, work & relationships, development, cognition) and a specific question. |
| Choose approach | Open, direct, empathic, structured, challenging, silence. Approach × patient disposition changes rapport and what is disclosed. |
| Observe | Appearance, behaviour, speech, mood/affect, thought form/content, perception, cognition, insight, judgement. Accuracy scales with the player's observation skill; some signs appear only at particular moments. |
| Assess | Structured rating scale, cognitive screen, risk assessment framework. More reliable, slower, can strain rapport if badly timed. |
| Investigate | Order fictional lab panels / imaging / substance screen (results arrive later); request old records; ask nursing staff. |
| Collateral | Call family, school, referrer — needs consent under the game's rules, except in defined emergencies. |
| Formulate | Build the differential (§5). |
| Plan | Treatment plan and disposition (§6). |
| Document | Write the note (§3.2). |

### 4.2 Patient response model

Each question targets one or more hidden facts. Whether and how the patient answers
depends on rapport, guardedness for that topic, insight, the chosen approach, the
patient's personality and how the session has gone so far. Possible results: clear
disclosure, partial, vague, denial, minimised or exaggerated value, irritation,
tearfulness, a tangent that reveals something unasked. The same question asked later
with better rapport can produce a different answer — and now the chart holds both,
dated.

Rapport and alliance persist across visits and feed adherence and follow-up
attendance. A patient who felt interrogated may not come back.

### 4.3 Time pressure

A clinic slot is finite. The player cannot ask everything; overrunning delays the
next patient (waiting-room consequences, productivity KPI) while under-assessing
risks a wrong formulation. "When is additional assessment needed?" is thus a real
decision with a price either way.

---

## 5. Formulation and diagnosis

- The player adds hypotheses to a differential and may link findings as *supporting*
  or *against*. The game does **not** display a truth probability.
- What the game does show is an *evidence summary* computed only from what the
  player has found: which expected features of each chosen hypothesis are present,
  absent, or not yet assessed. This rewards knowledge and thoroughness without
  revealing the answer.
- The player commits a working diagnosis (or explicitly defers: "further assessment
  needed") and can revise it at any later visit; the chart keeps the history.
- Feedback arrives the way it does in life: the patient's course, a supervisor's
  critique (trainee/resident ranks), a colleague's second opinion, a case review
  after an incident. A wrong diagnosis is recoverable if noticed; persisting with it
  has consequences.

Internally the `inference` kernel holds a likelihood table (condition profile ×
finding) from data. It is used for evidence summaries, for supervisor critiques
("you did not explore past elevated mood, which matters for this differential"),
for the auto-resolve policy bot, and for the solver tests in §10.

---

## 6. Treatment, disposition and follow-up

**Treatment plan** = any combination of:

- talking-therapy classes (supportive, structured, family-based, group, trauma-focused),
- medication classes (abstract: mood-lifting, calming, stabilising,
  thought-organising, sleep-supporting, attention-supporting) at abstract intensity
  (low / standard / high),
- social interventions (social-work referral, housing/employment support, family meeting),
- monitoring (observation level, check-in calls),
- referrals to other professionals (psychologist, physician, specialist team).

Each has a hidden per-patient response value, an onset delay, possible side effects
(also simulated: the patient may stop because of them and not tell you), and
interactions with adherence and alliance.

**Disposition** (under the fictional country's Mental Health Code):

| Option | Rule in the game |
|---|---|
| Discharge to referrer | Allowed any time; an incident soon after is reviewed against your documented risk assessment. |
| Outpatient follow-up | Choose interval; the patient's condition evolves in between; no-shows are possible. |
| Voluntary admission | Needs patient agreement and a bed. |
| Safety hold (involuntary) | Requires documented evidence of serious, imminent risk meeting listed criteria; a senior must countersign at trainee/resident ranks; an independent review hearing follows within 3 game days and can overturn it. |

Both over- and under-use of holds have consequences: harm and incident review on
one side; overturned holds, complaints, lost trust and a patient who avoids services
on the other. There is no option that is always safe.

**Follow-ups** go on the agenda. Continuity is modelled: seeing your own patient
again preserves rapport and context; a patient seen by a colleague on your day off
comes back with that colleague's note in the chart (generated by the same simulation).

---

## 7. Patient progression

Between contacts, `on_days_advanced` steps every active case daily:

```
symptom(t+1) = symptom(t)
             + natural_course(condition, trajectory, t)
             − treatment_effect(match × intensity × adherence × alliance, onset_delay)
             + stressor_impact(life events of the patient as a Person)
             + side_effect_burden
             ± bounded noise (career RNG stream)
```

Thresholds produce state changes: improvement, remission, relapse, deterioration,
crisis presentation to the emergency area, disengagement, complaint, self-discharge.
Inpatients additionally respond to observation level, ward milieu and staffing.
Because patients are world persons, their own life events (bereavement, job loss,
new relationship) are real inputs — and occasionally involve people the player knows.

---

## 8. Hospital events and professional decisions

Delivered through the global event engine using a psychiatry event pack, bound to
real staff and patients:

- **Clinical**: emergency admission during clinic; inpatient deterioration at 03:00
  on call; unexpected test result; a patient refusing the plan; a family demanding
  admission — or demanding discharge.
- **Team**: staffing shortage forcing prioritisation; disagreement with a nurse who
  knows the patient better than you; a supervisor whose advice you think is wrong; a
  colleague's error you noticed; a rival for the same post.
- **Ethical**: confidentiality vs. warning a third party; a gift from a patient; a
  patient who is a friend's relative; pressure to discharge to free a bed; a request
  to alter a note.
- **Administrative**: bed crisis, budget cut, policy change, audit of your notes,
  complaint investigation, hospital inspection (your documentation and incident
  record are the evidence).

Storylines link them: e.g. *shortage → rushed discharge → readmission → case review
→ your statement → relationship with the unit manager*, each step conditional on
what you actually did.

---

## 9. Progression and specializations

| Rank | What changes in play |
|---|---|
| **Trainee** | Small supervised caseload; every plan reviewed; supervisor feedback is the game's diegetic tutorial; cannot authorise holds alone; exam Part 1. |
| **Resident** | Larger caseload; on-call nights and emergency assessments; first specialization rotations; board exam. |
| **Attending** | Own patients and clinic; final say on dispositions; supervises a trainee (you now review *their* notes and decide when to step in). |
| **Senior specialist** | Complex referrals and second opinions; specialization depth; teaching; expert reports. |
| **Department director** | `org` kernel: rota and vacancies, budget lines, policies (e.g. observation standards), handling complaints and staff conflict, inspection readiness — with a reduced clinical list. |
| **Hospital administrator** | Hospital-wide finance and strategy, external relations, crises and inspections; decisions shape the conditions every clinician (NPC) works in. |

Promotion is handled by `CareerHost` from module KPIs: diagnostic accuracy (judged
retrospectively), outcomes, safety incidents weighed against documented reasoning,
documentation quality, timeliness, patient feedback, team relationships, exams.

**Specializations** change the case mix and add mechanics:

- **Adult** — the baseline; broadest condition mix.
- **Child & adolescent** — the patient rarely tells the whole story; parents and
  school are essential and sometimes conflicting sources; consent and family
  dynamics drive decisions.
- **Forensic** — court-requested assessments under the fictional code; detecting
  inconsistency and feigning; writing reports that are tested in hearings.
- **Geriatric** — separating decline, low mood and acute physical causes; capacity
  judgements; family conflict about care.

---

## 10. How we will know it works (tests planned for Milestone 5)

- **Solvability**: for every generated case, a thorough-policy bot can obtain
  findings sufficient to rank the true condition first.
- **Skill matters**: thorough > average > careless policies on diagnostic accuracy
  and outcomes, by a margin, over thousands of seeded cases.
- **Treatment matters**: matched plans beat mismatched plans beat no plan; over-
  treatment has measurable costs.
- **No dominant strategy**: "admit everyone", "discharge everyone" and "ask
  everything" each score worse overall than balanced play.
- **Consistency**: a patient's answers never contradict their hidden truth except
  through their modelled disclosure tendencies; chart findings always trace to an
  action that produced them.
- **Persistence**: save mid-consultation → load → identical state; patient histories
  intact across years of game time.
- **Parity**: `auto_resolve_shift` and interactive shifts run the same code path and
  yield the same kinds of records.

---

## 11. First playable slice (Milestone 5 target)

One complete trainee day, repeatable across weeks:

1. Morning handover (2 inpatients).
2. Outpatient clinic: 1 new assessment + 2 follow-ups.
3. Ward review of the inpatients.
4. One unscheduled emergency assessment with a disposition decision.
5. Documentation and supervision feedback.
6. End-of-shift report → KPIs → the life simulation resumes (stress, pay,
   relationships, the evening's agenda).

Minimum content for the slice: ~12 condition profiles, ~70 findings, ~120
questions, ~30 treatments/interventions, ~40 hospital events, ~12 named staff.
The rest of Milestone 5 extends the slice across the four clinical ranks (trainee,
resident, attending, senior specialist) with the adult specialization. The two
management ranks and the child, forensic and geriatric specializations are designed
above but scheduled for Milestone 6 (see `ROADMAP.md`).
