# BPMN Learn & Grade (BLG)

**BPMN Learn & Grade (BLG)** is a web-based tool for grading student BPMN (Business Process Model and Notation) submissions. BLG lets educators define rubrics, build behavioral validation rules, and grade student work against a reference model.

This repository is a monorepo containing both the REST API back-end (`backend/`) and the Vue.js front-end (`frontend/`).

---

## Architecture

```
blg/
├── backend/                       # FastAPI back-end
│   ├── main.py                    # Entry point
│   ├── checks/                    # Grading logic & rule engine
│   ├── routers/                   # API routes
│   ├── bpmn/                      # BPMN XML parser
│   ├── rules/                     # Behavioral rule manager
│   ├── rubric/                    # Rubric models
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
- **Rubric management**: Define criteria with point values; supports simple checks and group criteria with XOR/AND logic.
- **Visual rule builder**: Node-based editor to build behavioral validation rules (element checks, gateway checks, connectors).
- **BPMN viewer**: Side-by-side view of student submission, reference model, and assignment PDF.
- **Auto-grading interface**: Grade submissions against rubric criteria; highlights non-compliant BPMN elements.
- **Onboarding wizard**: Step-by-step setup for uploading a reference model and configuring the initial rubric.

### Back-end (API)
- **Automated grading**: runs a configurable set of structural, semantic and behavioral checks against student BPMN submissions.
- **Behavioral rule engine**: graph-based workflow rules (nodes + edges) capture expected BPMN sequences; evaluated with AND/XOR branch logic.
- **Semantic similarity**: uses `sentence-transformers/all-mpnet-base-v2` for label matching so minor wording differences don't break grading.
- **Formal control-flow analysis**: deadlock and dead-activity detection.
- **Excel export**: per-submission and bulk grading results exportable as `.xlsx`.
- **Rule groups**: combine multiple behavioral rules under XOR (alternative solutions) or AND (all required) conditions.

---

## Prerequisites

| Tool | Purpose |
|---|---|
| Python ≥ 3.10 | Back-end runtime |
| Node.js ≥ 20 (or [Bun](https://bun.sh/)) | Front-end runtime |
| Docker | Containerized deployment (optional) |

> [`uv`](https://github.com/astral-sh/uv) (Python) and [`bun`](https://bun.sh/) (Node) are optional but recommended for faster installs. Where available they are used automatically on Linux/macOS via the Makefile.

---

## Installation & Running

### Docker (all platforms)

The easiest way to run the full stack on any operating system:

```bash
docker compose up --build -d   # build & start at http://localhost:8000
docker compose down
```

Because `docker-compose.yml` mounts `./backend/assignment` into the container, any rubrics or rules you create in the web UI are saved to your local `backend/assignment` folder. The backend scaffolds the required subdirectories (`submissions/`, `rules/`, `templates/`) on first run.

> **Linux:** you may need `sudo`, or add your user to the `docker` group first.

---

### Linux & macOS

A `Makefile` at the repo root simplifies setup and execution. It auto-detects `uv`/`pip` and `bun`/`npm`.

**1. Install all dependencies:**
```bash
make install
```

**2. Start the back-end** (data root defaults to `./assignment`, port 8000):
```bash
make run-backend
make run-backend DATA_DIR=my_class_data   # custom data directory
```

The back-end will automatically create the data root and initialize its folder structure if it doesn't exist.

**3. Start the front-end** dev server at `http://localhost:5173` (in a new terminal):
```bash
make run-frontend
```

**Production build** - compile the front-end and serve it from the back-end on port 8000:
```bash
make build-frontend
make run-backend
```

---

### Windows

The Makefile relies on Unix shell utilities and does not work natively on Windows. Use one of the options below.

#### Option A - WSL2 (recommended)

Install [WSL2](https://learn.microsoft.com/en-us/windows/wsl/install) with Ubuntu, then open a WSL terminal and follow the **Linux & macOS** instructions above.

#### Option B - PowerShell (manual)

```powershell
# --- Install ---
cd backend
pip install .                          # or: uv sync
cd ..\frontend
npm install                            # or: bun install

# --- Run back-end (from backend\) ---
python main.py ..\assignment           # replace 'assignment' with your data directory

# --- Run front-end (from frontend\, in a new terminal) ---
npm run dev                            # or: bun run dev

# --- Production build (from frontend\) ---
npm run build                          # or: bun run build
Remove-Item -Recurse -Force ..\backend\static
Copy-Item -Recurse dist ..\backend\static
```

---

## API Overview (Back-end)

Interactive API docs are available at `http://127.0.0.1:8000/docs` when the back-end is running.

| Method   | Path                                        | Description                              |
|----------|---------------------------------------------|------------------------------------------|
| `GET`    | `/api/rubric`                               | Fetch the current rubric                 |
| `POST`   | `/api/rubric`                               | Create a rubric via onboarding payload   |
| `DELETE` | `/api/rubric/criteria/{id}`                 | Remove a rubric criterion                |
| `GET`    | `/api/submissions`                          | List all student submissions             |
| `POST`   | `/api/submissions`                          | Upload `.bpmn` files                     |
| `GET`    | `/api/submissions/{filename}`               | Download raw BPMN XML                    |
| `GET`    | `/api/submissions/export`                   | Export a single result as `.xlsx`        |
| `GET`    | `/api/submissions/export/all`               | Export all results as `.xlsx`            |
| `GET`    | `/api/checks`                               | List all registered checks               |
| `POST`   | `/api/checks/analyze`                       | Analyze a submission against the rubric  |
| `POST`   | `/api/checks/analyze/all`                   | List applicable checks for a given model |
| `GET`    | `/api/behavioral-rules`                     | List behavioral rules                    |
| `POST`   | `/api/behavioral-rules`                     | Create a rule                            |
| `PUT`    | `/api/behavioral-rules/{id}`                | Update a rule                            |
| `DELETE` | `/api/behavioral-rules/{id}`                | Delete a rule                            |
| `POST`   | `/api/behavioral-rules/{id}/validate`       | Validate a rule against a BPMN model     |
| `GET`    | `/api/behavioral-rule-groups`               | List rule groups                         |
| `POST`   | `/api/behavioral-rule-groups`               | Create a rule group                      |
| `PUT`    | `/api/behavioral-rule-groups/{id}`          | Update a rule group                      |
| `DELETE` | `/api/behavioral-rule-groups/{id}`          | Delete a rule group                      |
| `POST`   | `/api/behavioral-rule-groups/{id}/validate` | Validate a group against a BPMN model    |

---

## Adding a New Check

1. Create a `.py` file in `backend/checks/implementations/`.
2. Subclass `Check` and define the required `ClassVar` fields (`id`, `name`, `description`, `check_complexity`, `input_scheme`).
3. Implement `analyze()` and `is_applicable()`.

The check is auto-discovered and registered on the next server start with no additional wiring required.

---

## Linting & Formatting

Run from `backend/`. Configured in `pyproject.toml` (rules: E, F, UP; double-quote style).

```bash
# Linux/macOS
ruff check . && ruff format .

# Windows (PowerShell)
ruff check .; ruff format .
```
