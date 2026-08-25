# BPMN Learn & Grade (BLG)

**BPMN Learn & Grade (BLG)** is a web-based tool for grading student BPMN (Business Process Model and Notation) submissions. BLG lets educators define rubrics, build behavioral validation rules, and grade student work against a reference model.

![Grading interface](docs/images/grading-view.png)

---

## Features

### Front-end (UI)
- **Assignment management**: A landing page to pick an existing assignment or create a new one; each assignment has its own rubric, rules, and submissions.
- **Submission upload**: Upload student `.bpmn` files directly from the grading interface, so no manual file copying is required.
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

## Screenshots

**Assignments landing page**: pick an existing assignment or create a new one:

![Assignments landing page](docs/images/project-view.png)

**Onboarding wizard**: upload a reference model and configure the initial rubric:

![Onboarding wizard](docs/images/onboarding-view.png)

**Visual rule builder**: build behavioral validation rules from a node-based editor:

![Visual rule builder](docs/images/behavioral-rule-view.png)

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

Because `docker-compose.yml` mounts `./backend/data` into the container, any assignments, rubrics, rules, and uploaded submissions you create in the web UI are saved to your local `backend/data` folder. The backend scaffolds the data layout (`assignments/` and a global `templates/`) on first run; each assignment gets its own `submissions/`, `rules/`, and rubric.

> **Linux:** you may need `sudo`, or add your user to the `docker` group first.

---

### Linux & macOS

A `Makefile` at the repo root simplifies setup and execution. It auto-detects `uv`/`pip` and `bun`/`npm`.

**1. Install all dependencies:**
```bash
make install
```

**2. Start the back-end** (data root defaults to `./data`, port 8000):
```bash
make run-backend
make run-backend DATA_DIR=my_class_data   # only needed for a non-default data directory
```

You don't normally need to set `DATA_DIR`; the back-end serves all your assignments from a single data root, and you pick or create individual assignments from the landing page in the web UI. Only override it if you want to keep your data somewhere other than `./data`. The back-end automatically creates the data root and initializes its folder structure if it doesn't exist.

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
python main.py ..\data                 # data root; assignments are managed from the web UI

# --- Run front-end (from frontend\, in a new terminal) ---
npm run dev                            # or: bun run dev

# --- Production build (from frontend\) ---
npm run build                          # or: bun run build
Remove-Item -Recurse -Force ..\backend\static
Copy-Item -Recurse dist ..\backend\static
```

---

## Using the app

Once the back-end and front-end are running, open the app in your browser and:

1. **Pick or create an assignment** on the landing page. Each assignment is self-contained (its own reference model, rubric, rules, and submissions) and lives under `assignments/` in the data root, so there's no need to point the back-end at a different data directory per class.
2. **Complete onboarding** for a new assignment: upload the reference BPMN model and configure the initial rubric.
3. **Upload student submissions** as `.bpmn` files from the grading interface.
4. **Grade** each submission against the rubric and export results to `.xlsx`.

---

## Demo deployment (read-only)

For hosting a public demo (e.g. on a VM), `docker-compose.demo.yml` adds a Traefik HTTPS ingress and enables a read-only demo mode:

- **The data root is mounted read-only.** Nothing in demo mode writes to it — grading results are computed and returned but never persisted — so the kernel enforcing that is what keeps the dataset pristine. There is no snapshot to restore and no reset job to run.
- **The demo is pinned to a single assignment** via `DEMO_PROJECT`. It is selected at startup, so visitors land straight in the grading UI, and it's the only project `POST /api/projects/{name}/select` will accept.
- Every mutating API endpoint returns 403. The few POST endpoints the UI genuinely needs — selecting the pinned project, analyzing a model, exporting to `.xlsx` — are allowlisted and none of them persist anything.
- Request bodies are capped at 2 MB, enforced on the bytes actually received (not on a `Content-Length` the client can omit).
- **The container runs unprivileged** as uid 1000, with `/app` root-owned — the app can read its code, venv and model but not modify them. The sentence-transformer weights (~420 MB) are baked into the image at build time and `HF_HUB_OFFLINE=1` is set, so the deployment never reaches out to the HuggingFace Hub at runtime.
- **Traefik has no access to the Docker socket.** It reads container labels through `tecnativa/docker-socket-proxy`, which permits only the list/inspect/events calls the provider needs and denies every state-changing call. The proxy sits on an `internal` network that the backend is not attached to. (Mounting the socket `:ro` is *not* equivalent — that only blocks writes to the socket file; every API call, including "create a privileged container", still goes through.)
- Traefik rate-limits requests. **This limit is global, not per-IP:** behind a WAF every request arrives from the WAF's address, so Traefik's default per-remote-address keying collapses into a single shared budget. Making it per-IP means trusting `X-Forwarded-For`, which is only safe once the VM is unreachable except through the WAF — otherwise anyone can spoof the header and bypass the limit. `docker-compose.demo.yml` has the two lines to uncomment when that holds.

Note that the backend keeps a single *server-wide* active project. With the demo pinned that's fixed, but it's worth knowing this is a single-user tool being demoed, not a multi-tenant one.

One-time setup on the host:

1. Put the demo data set somewhere outside the checkout, e.g. `/srv/blg-demo-data`, laid out as `assignments/<Name>/` plus `templates/`.
2. Click through it once with a writable copy locally. This caches `reference.bpmn.json` and any submission evaluations you want pre-graded — the read-only demo computes results on the fly but cannot write them back, so anything missing is simply recomputed per request.
3. Generate a TLS certificate (self-signed is fine, e.g. when behind a WAF): `scripts/gen-selfsigned-cert.sh your-demo-domain`
4. Make the data directory readable by uid 1000 (`sudo chown -R 1000:1000 /srv/blg-demo-data`), or pass `--build-arg UID=$(id -u) --build-arg GID=$(id -g)` at build time to match whoever owns it.

Start the demo:

```bash
export DEMO_DOMAIN=your-demo-domain
export DEMO_DATA_DIR=/srv/blg-demo-data   # defaults to ./backend/data
export DEMO_PROJECT=Webshop               # must match a directory under assignments/
docker compose -f docker-compose.yml -f docker-compose.demo.yml up -d --build
```

The first build downloads the model weights and is correspondingly slow; later builds reuse that layer unless the dependencies change.

Demo mode can also be enabled outside Docker by setting `DEMO_MODE=1` when starting the back-end (`1`/`true`/`yes`/`on` enable it; anything else, including `0` and `false`, leaves it off). Note that outside Docker nothing enforces the read-only data root — that comes from the `:ro` mount.
