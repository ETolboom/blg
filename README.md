# BPMN Learn & Grade (BLG)

**BPMN Learn & Grade (BLG)** is a web-based tool for grading student BPMN (Business Process Model and Notation) submissions. BLG lets educators define rubrics, build behavioral validation rules, and grade student work against a reference model.

This repository is a monorepo containing both the REST API back-end (`backend/`) and the Vue.js front-end (`frontend/`).

---

## Architecture

```
blg/
├── backend/                       # FastAPI back-end & Rust extensions
│   ├── main.py                    # Entry point
│   ├── checks/                    # Grading logic & rule engine
│   ├── routers/                   # API routes
│   ├── bpmn/                      # BPMN XML parser
│   ├── rules/                     # Behavioral rule manager
│   ├── rubric/                    # Rubric models
│   ├── src/                       # Rust source for formal control-flow analysis
│   └── example/                   # Sample data (rubric, submissions, rules)
├── frontend/                      # Vue 3 + PrimeVue front-end
│   ├── src/                       # Components, Views, router
│   ├── package.json
│   └── vite.config.ts
├── docker-compose.yml             # Orchestration
├── Makefile                       # Development helpers
└── README.md
```

---

## Features

### Front-end (UI)
- **Rubric management** — Define criteria with point values; supports simple checks and group criteria with XOR/AND logic.
- **Visual rule builder** — Node-based editor to build behavioral validation rules (element checks, gateway checks, connectors).
- **BPMN viewer** — Side-by-side view of student submission, reference model, and assignment PDF.
- **Auto-grading interface** — Grade submissions against rubric criteria; highlights non-compliant BPMN elements.
- **Onboarding wizard** — Step-by-step setup for uploading a reference model and configuring the initial rubric.

### Back-end (API)
- **Automated grading** — runs a configurable set of structural, semantic and behavioral checks against student BPMN submissions.
- **Behavioral rule engine** — graph-based workflow rules (nodes + edges) capture expected BPMN sequences; evaluated with AND/XOR branch logic.
- **Semantic similarity** — uses `sentence-transformers/all-mpnet-base-v2` for label matching so minor wording differences don't break grading.
- **Formal control-flow analysis** — deadlock and dead-activity detection via a compiled Rust extension.
- **Excel export** — per-submission and bulk grading results exportable as `.xlsx`.
- **Rule groups** — combine multiple behavioral rules under XOR (alternative solutions) or AND (all required) conditions.

---

## Prerequisites

| Tool | Purpose |
|---|---|
| Python ≥ 3.10 | Back-end Runtime |
| Node.js ≥ 20 | Front-end Runtime |
| Docker (Optional) | Containerized deployment |

---

## Local Development (Native)

For convenience, a `Makefile` is provided at the root of the repository to simplify setup and execution.

### 1. Installation

Install all dependencies in one go:

```bash
make install
```

### 2. Running the Back-end

The back-end requires a "data root" directory where it looks for files like `reference.bpmn`, `rubric.json`, and nested directories for submissions and rules. 

If the directory doesn't exist, the backend will **automatically create it** and initialize the required folder structure (`submissions/`, `rules/`, `templates/`).

You can run the back-end (which defaults to using `./assignment` as the data root):

```bash
make run-backend
```

To use a custom directory name:
```bash
make run-backend DATA_DIR=my_class_data
```

### 3. Running the Front-end

In a new terminal, start the Vite development server:

```bash
make run-frontend
```

The UI will be available at `http://localhost:5173`.

### Bundling for Production

You can build the front-end and have the back-end serve it automatically (so both run on port 8000).

```bash
make build-frontend
make run-backend
```

---

## Docker Deployment

You can run the entire stack using Docker Compose:

```bash
make docker-up
# or manually: docker compose up --build -d
```

Because `docker-compose.yml` mounts `./backend/assignment` to `/app/example` by default, any rubrics or rules you create in the web UI will be saved to your local `backend/assignment` folder on your host machine. The backend will automatically scaffold the directories inside it on the first run.

- **App URL**: `http://localhost:8000`

To stop the container:

```bash
make docker-down
```

---

## API Overview (Back-end)

Interactive API docs are available at `http://127.0.0.1:8000/docs` when the back-end is running.

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/rubric` | Fetch the current rubric |
| `POST` | `/api/rubric` | Create a rubric via onboarding payload |
| `DELETE` | `/api/rubric/criteria/{id}` | Remove a rubric criterion |
| `GET` | `/api/submissions` | List all student submissions |
| `POST` | `/api/submissions` | Upload `.bpmn` files |
| `GET` | `/api/submissions/{filename}` | Download raw BPMN XML |
| `GET` | `/api/submissions/export` | Export a single result as `.xlsx` |
| `GET` | `/api/submissions/export/all` | Export all results as `.xlsx` |
| `GET` | `/api/checks` | List all registered checks |
| `POST` | `/api/checks/analyze` | Analyze a submission against the rubric |
| `POST` | `/api/checks/analyze/all` | List applicable checks for a given model |
| `GET` | `/api/behavioral-rules` | List behavioral rules |
| `POST` | `/api/behavioral-rules` | Create a rule |
| `PUT` | `/api/behavioral-rules/{id}` | Update a rule |
| `DELETE` | `/api/behavioral-rules/{id}` | Delete a rule |
| `POST` | `/api/behavioral-rules/{id}/validate` | Validate a rule against a BPMN model |
| `GET` | `/api/behavioral-rule-groups` | List rule groups |
| `POST` | `/api/behavioral-rule-groups` | Create a rule group |
| `PUT` | `/api/behavioral-rule-groups/{id}` | Update a rule group |
| `DELETE` | `/api/behavioral-rule-groups/{id}` | Delete a rule group |
| `POST` | `/api/behavioral-rule-groups/{id}/validate` | Validate a group against a BPMN model |

Interactive API docs are available at `http://127.0.0.1:8000/docs` when the server is running.

---

## Adding a New Check

1. Create a `.py` file in `backend/checks/implementations/`.
2. Subclass `Check` and define the required `ClassVar` fields (`id`, `name`, `description`, `check_complexity`, `input_scheme`).
3. Implement `analyze()` and `is_applicable()`.

The check is auto-discovered and registered on the next server start — no wiring required.

---

## Linting & Formatting

```bash
ruff check .
ruff format .
```

Configured in `pyproject.toml` (rules: E, F, UP; double-quote style).