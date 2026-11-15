# Original Brief — LIFEVERSE

_Received from the project owner on 2026-11-15. Reproduced verbatim (only heading
markup added). Sections are referenced elsewhere as `B1` … `B15`._

---

PROJECT: LIFEVERSE — ADVANCED LIFE & CAREER SIMULATION GAME

You are the lead game architect, senior gameplay programmer, simulation engineer, UI/UX designer, technical director, and QA engineer responsible for developing an ambitious commercial-quality life simulation game.

Your task is to design and develop a complete, deeply interactive life simulation inspired by the accessibility of BitLife, but significantly more sophisticated in its professional gameplay, character simulation, world persistence, and decision-making systems.

This must NOT be a simple text-based BitLife clone.

The central design philosophy is:

Every profession must feel like its own playable simulation game inside a larger persistent life simulator.

The player must actually perform professional activities, interact with systems, make decisions, investigate cases, manage responsibilities, and experience consequences.

Do not create fake functionality, decorative buttons, disconnected systems, or features that merely pretend to work.

## B1. TECHNOLOGY AND DEVELOPMENT ENVIRONMENT

Use:

* Godot 4, using the currently supported stable version.
* GDScript with strongly structured, maintainable architecture.
* Blender for optional 3D environments, characters, animations, and assets.
* Data-driven systems using JSON or Godot Resources where appropriate.
* SQLite or another suitable persistence solution if justified.
* Modular architecture allowing new professions to be added without rewriting the entire game.

The primary experience should be a sophisticated 2D interface with optional 3D environments for professional activities.

First inspect the actual development environment, installed software, project structure, and available tools.

Never assume an integration exists without verifying it.

## B2. CORE LIFE SIMULATION

Develop a persistent character life system containing:

* Birth and character creation.
* Name, appearance, gender, personality, and background.
* Family members and family history.
* Childhood development.
* School and education.
* University and professional training.
* Employment and career progression.
* Relationships and friendships.
* Dating, marriage, divorce, and children.
* Pregnancy and family development.
* Financial management.
* Housing and property ownership.
* Physical and psychological well-being as fictional simulation attributes.
* Aging and life stages.
* Retirement and death.
* Legacy and generational continuation.

Characters must have persistent identities, histories, memories, preferences, and relationships.

The world must remember important events.

## B3. ADVANCED CHARACTER AI AND SOCIAL SIMULATION

Each important NPC must have:

* Individual personality.
* Personal goals.
* Strengths and weaknesses.
* Emotional states.
* Relationship history.
* Personal memories.
* Family relationships.
* Career and financial situation.
* Individual preferences.
* Reactions to the player’s behavior.

NPCs should not behave as interchangeable random event generators.

Develop a relationship simulation where past decisions influence future interactions.

Implement social consequences, trust, conflict, reputation, friendships, rivalries, and long-term relationships.

## B4. PROFESSIONAL CAREER SIMULATION FRAMEWORK

This is one of the most important systems in the game.

Create a modular career framework.

Every career must contain:

* Professional progression.
* Qualifications and education requirements.
* Work schedules and shifts.
* Work environments.
* Professional tools and interfaces.
* Daily responsibilities.
* Interactive tasks.
* Professional decisions.
* Performance evaluation.
* Income and expenses.
* Promotions.
* Professional reputation.
* Consequences of poor decisions.
* Specialized career branches.

Do not implement careers as simple buttons that award money.

Create reusable technical systems that allow completely different professional gameplay modules.

## B5. PSYCHIATRY CAREER — FIRST DEEP PROFESSIONAL MODULE

The first fully developed career must be psychiatry.

Build a detailed psychiatric hospital simulation.

The player should work as a psychiatrist and actually perform professional activities.

Include:

A. Hospital environment:

* Reception.
* Waiting rooms.
* Consultation offices.
* Psychiatric inpatient units.
* Staff offices.
* Medical records department.
* Emergency psychiatric assessment areas.
* Treatment and observation rooms.

B. Patient management:

* Individually generated fictional patients.
* Persistent patient identities.
* Personal histories.
* Family backgrounds.
* Medical histories.
* Presenting complaints.
* Symptoms.
* Behavioral observations.
* Previous treatments.
* Follow-up appointments.
* Patient-specific progression.

C. Clinical records:

* Detailed patient charts.
* Medical history.
* Psychiatric history.
* Family history.
* Clinical observations.
* Medication history.
* Previous diagnoses.
* Assessment notes.
* Treatment plans.
* Follow-up documentation.

D. Interactive consultations:

* Ask questions.
* Select interview approaches.
* Observe patient behavior.
* Identify relevant symptoms.
* Review medical records.
* Compare reported information.
* Evaluate fictional clinical scenarios.
* Formulate diagnostic hypotheses.
* Select appropriate simulated treatment plans.
* Schedule follow-up appointments.

E. Professional decisions:

* Determine when additional assessment is needed.
* Evaluate patient safety in fictional scenarios.
* Decide whether hospitalization is appropriate within the game’s fictional rules.
* Manage disagreements with patients.
* Handle difficult family interactions.
* Coordinate with other professionals.
* Evaluate treatment progress.

F. Hospital events:

* Emergency admissions.
* Patient deterioration.
* Unexpected clinical situations.
* Staffing shortages.
* Professional conflicts.
* Ethical dilemmas.
* Administrative decisions.
* Hospital inspections.

G. Professional progression:

* Psychiatrist trainee.
* Resident.
* Attending psychiatrist.
* Senior specialist.
* Department director.
* Hospital administrator.

Include possible specializations such as child and adolescent psychiatry, forensic psychiatry, geriatric psychiatry, and adult psychiatry.

All medical cases must be fictional simulations, with internally consistent outcomes and no presentation as real-world diagnostic or prescribing guidance.

## B6. FUTURE PROFESSIONAL MODULES

Design the architecture to support these additional careers:

MEDICINE:

* General practitioner.
* Surgeon.
* Emergency physician.
* Pediatrician.
* Neurologist.
* Nurse.

LAW:

* Criminal defense lawyer.
* Prosecutor.
* Judge.
* Corporate lawyer.

CRIMINAL JUSTICE:

* Police officer.
* Detective.
* Forensic investigator.
* Criminal analyst.

EDUCATION:

* School teacher.
* University professor.
* School administrator.
* Academic researcher.

BUSINESS:

* Entrepreneur.
* CEO.
* Financial analyst.
* Real estate investor.

CREATIVE PROFESSIONS:

* Fashion designer.
* Makeup artist.
* Interior designer.
* Photographer.
* Actor.
* Music producer.

Each career must eventually have its own dedicated gameplay mechanics, not just different descriptions.

## B7. DYNAMIC EVENT AND CONSEQUENCE ENGINE

Build a sophisticated event engine.

Events must depend on:

* Character age.
* Personality.
* Relationships.
* Education.
* Career.
* Financial situation.
* Previous decisions.
* Current circumstances.
* World events.

Events must have branching choices and persistent consequences.

The system should support complex chains of events.

Example:

A character meets someone during university.

Their relationship develops over time.

They may become friends, romantic partners, enemies, or lose contact.

Years later, their relationship history can affect employment opportunities, family events, financial decisions, or unexpected encounters.

Avoid disconnected random events.

## B8. EDUCATION AND UNIVERSITY SIMULATION

Include:

* School enrollment.
* Classes.
* Examinations.
* Grades.
* Academic performance.
* Student relationships.
* University applications.
* Degrees.
* Professional qualifications.
* Tuition and student expenses.
* Academic failures and achievements.
* Career eligibility.

Different degrees should unlock different career paths.

## B9. FINANCIAL AND ECONOMIC SIMULATION

Implement:

* Salary and bonuses.
* Bank accounts.
* Expenses.
* Taxes.
* Rent and mortgages.
* Property purchases.
* Investments.
* Businesses.
* Loans.
* Debt.
* Inheritance.
* Retirement savings.

The financial system must affect actual gameplay.

## B10. GAME INTERFACE AND PRESENTATION

Create a professional, modern, polished interface.

Required interfaces:

* Character dashboard.
* Life timeline.
* Relationships.
* Family tree.
* Education.
* Career dashboard.
* Professional workspaces.
* Financial dashboard.
* Event system.
* Character profiles.
* NPC interaction interface.
* Settings and accessibility.

The interface must be visually coherent and responsive.

Use animations, transitions, detailed icons, visual indicators, and clear information hierarchy.

Avoid generic placeholder interfaces.

## B11. SAVE SYSTEM AND WORLD PERSISTENCE

Create a robust save/load architecture.

Persist:

* Character data.
* NPC identities.
* Relationships.
* Career progression.
* Professional cases.
* Patient histories.
* Decisions and consequences.
* Financial state.
* Family generations.
* World events.

The player must be able to close the game and continue exactly where they left off.

## B12. TECHNICAL ARCHITECTURE

Design independent modules for:

* Character simulation.
* NPC simulation.
* Relationships.
* Event generation.
* Career simulation.
* Professional case management.
* Education.
* Economy.
* Time and aging.
* World persistence.
* UI.
* Save/load.

Use clear interfaces between modules.

Avoid monolithic scripts.

Use data-driven content so that adding hundreds of new events or cases does not require rewriting the game engine.

Create documentation and automated tests.

## B13. DEVELOPMENT METHODOLOGY

IMPORTANT: Do not attempt to build the entire game in one uncontrolled operation.

Work in milestones.

MILESTONE 1:
Research the project requirements, inspect the environment, compare appropriate technical approaches, and create the complete architecture document.

MILESTONE 2:
Build the playable life simulation foundation.

MILESTONE 3:
Implement character creation, aging, education, relationships, and event consequences.

MILESTONE 4:
Implement the professional career framework.

MILESTONE 5:
Develop the complete first playable psychiatry career module.

MILESTONE 6:
Implement advanced NPC behavior, persistence, and additional professional modules.

MILESTONE 7:
Polish the UI, performance, accessibility, and gameplay.

MILESTONE 8:
Perform comprehensive testing and prepare a playable release build.

At the end of every milestone:

* Run the game.
* Test implemented functionality.
* Fix discovered errors.
* Verify save/load.
* Document completed features.
* List incomplete features honestly.
* Provide the next development plan.

## B14. STRICT DEVELOPMENT RULES

1. Never claim a feature works unless it has been implemented and tested.
2. Never create fake buttons or nonfunctional interactions.
3. Never silently remove existing functionality.
4. Never overwrite working code without inspecting it.
5. Never create unnecessary duplicate systems.
6. Never use placeholder data as if it were a completed simulation.
7. Never sacrifice architectural quality for superficial speed.
8. Use automated tests wherever practical.
9. Keep a development log.
10. Maintain a PROJECT_STATUS.md file.
11. Maintain a technical architecture document.
12. Maintain a list of known bugs and unresolved tasks.
13. Verify all dependencies and APIs against their actual documentation.
14. Prioritize a working playable experience over an enormous unfinished feature list.

## B15. FIRST TASK — DO NOT START CODING RANDOMLY

Before writing the game:

1. Analyze the entire project vision.
2. Research suitable Godot architecture and implementation techniques.
3. Identify technical risks and difficult systems.
4. Estimate the workload.
5. Design the complete project directory structure.
6. Define the data models.
7. Define the event and consequence architecture.
8. Define the professional career plugin architecture.
9. Design the first playable psychiatry experience.
10. Create a realistic development roadmap.

Present your technical plan, architectural decisions, and first milestone.

Then begin implementation after the architecture has been reviewed.

The final objective is to deliver a genuinely playable, expandable, deeply immersive life simulation game where the player experiences an entire life and can meaningfully perform different professions.

Think like a professional game studio, build like a senior engineering team, and verify everything.
