Three artefacts configure an assignment in BLG. This page explains each one and how they relate to each other.

> **Video walkthrough:** *coming soon.*

---

## The Rubric

The rubric is the complete list of [criteria](Glossary#criterion--check) used to grade every submission for an assignment. Each criterion specifies:

| Field | Description |
|-------|-------------|
| **Name** | Displayed to the instructor in the grading view |
| **Description** | A short explanation of what the criterion checks |
| **Layer** | 1, 2 or 3 (determines how the criterion is evaluated) |
| **Inputs** | Configuration values for LAYER 2 criteria (e.g. pool/lane names) |
| **Default points** | Points awarded when the criterion is fulfilled |

### Creating a rubric (onboarding)
The rubric is built during *onboarding*: the instructor uploads a reference BPMN model, selects which checks to include, and configures any LAYER 2 inputs. LAYER 3 criteria (Behavioral Rules) are added separately.

### Changing the rubric
Modifying the rubric (adding, removing, or reconfiguring a criterion) invalidates all cached grading results. The next time a submission is analyzed, BLG re-grades it from scratch.

### Exporting results
Results can be exported per submission or in bulk as `.xlsx` files. Each row in the export corresponds to a criterion, showing the criterion name, description, and points awarded.

---

## The Reference BPMN Model

The reference model is the instructor's BPMN model representing a correct (or exemplary) solution to the assignment. It is used by:

- **LAYER 2** (Pool-Lane Check, Task Type, Task Coverage): the reference model pre-populates the check inputs during onboarding (e.g. expected pools/lanes, task types, and Task Coverage's list of expected tasks).
- **LAYER 3** (Behavioral Rules): the reference model is evaluated against each behavioral rule when the rule is validated.

The reference model is stored in `reference.bpmn` inside the data directory, separate from the rubric JSON. It is not included in grading exports.

### Uploading the reference model
The reference model is uploaded during onboarding via the BLG interface. It can be replaced afterwards by editing the reference from the grading view (the Reference tab) or by running onboarding again.

> **Note:** Changing the reference model does not automatically update existing behavioral rules. Each rule should be re-validated after a reference model change.

---

## The Supplement

The supplement is an optional **PDF document** attached to an assignment. Students can view it alongside the BPMN modeling interface. Typical uses include:

- A written description of the business process to be modeled.
- A narrative or case study students must translate into a BPMN diagram.
- Constraints or requirements that are difficult to express in a BPMN reference model.

### Uploading a supplement
The supplement can be uploaded and replaced at any time from the rubric settings in the BLG interface. Only PDF files up to 10 MB are accepted.

### Accessing the supplement
Once uploaded, the supplement is served at `/api/rubric/supplement` and displayed inline in the front-end.

---

## Data Directory Layout

BLG is multi-project. The server is given a **data root** that holds one folder per assignment under `assignments/`, plus a single global `templates/` directory shared across every assignment:

```
<data-root>/
├── assignments/
│   └── <assignment-name>/
│       ├── rubric.json          ← Rubric criteria (reference XML stored separately)
│       ├── reference.bpmn       ← Reference BPMN model
│       ├── reference.bpmn.json  ← Cached evaluation of the reference (generated, gitignored)
│       ├── supplement.pdf       ← Optional supplement PDF
│       ├── submissions/         ← Student .bpmn files and their cached <model>.bpmn.json results
│       └── rules/               ← Behavioral rule JSON files (groups: _group_<id>.json)
└── templates/                   ← Read-only reusable rule presets, shared across assignments
```

The data root is passed to the server at startup:

```bash
python main.py <data-root>
```

or, from the repo root:

```bash
make run-backend DATA_DIR=<data-root>   # defaults to ./data
```
