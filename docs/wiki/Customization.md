# Customization

BLG was designed for BPMN, but its architecture is not fundamentally BPMN-specific. This page describes how BLG can be adapted for other process modelling notations (e.g. UML Activity Diagrams, Petri nets, EPC) or extended with custom checks.

> **Status:** this page is a placeholder. Detailed guidance is planned for a future release.

---

## What is BPMN-specific?

The following parts of BLG are tied to BPMN:

| Component | BPMN-specific aspect |
|-----------|----------------------|
| `bpmn/bpmn.py` | Parses BPMN 2.0 XML (OMG namespace) |
| `bpmn/struct.py` | Data model uses BPMN concepts (Pool, Lane, PoolElement, FlowElement) |
| LAYER 1 control-flow checks | Call the Rust `blg` extension, which implements BPMN state-space analysis |
| LAYER 1 semantic checks | Work on task labels — portable, not BPMN-specific |
| LAYER 2 Pool-Lane Check | Checks BPMN pools and lanes |
| LAYER 3 Behavioral Rules | Traverse BPMN graph structure |

---

## Adapting for Another Notation (e.g. UML Activity Diagrams)

> *Detailed guide coming soon.*

High-level steps:

1. **Replace the parser.** Implement a new parser in `bpmn/` that reads the target notation's file format and produces the same `Pool`, `Lane`, `PoolElement`, `FlowElement` data structures. UML Activity Diagrams, for example, could be parsed from XMI.

2. **Replace or disable control-flow checks.** The Rust extension is BPMN-specific. For another notation, either skip LAYER 1 control-flow checks or implement equivalent analysis for the target formalism.

3. **Keep semantic and LAYER 2/3 checks.** Label-based checks (atomicity, duplicates, coverage) and behavioral rules work on the generic graph structure and should transfer with little or no modification.

4. **Adjust the file upload type.** The submissions router currently only accepts `.bpmn` files. Update the file extension validation in `services/submissions.py` to accept the target format.

---

## Adding a Custom LAYER 1 or LAYER 2 Check

New checks can be added without modifying any existing code:

1. Create a `.py` file in `checks/implementations/`.
2. Subclass `Check` (from `checks/__init__.py`).
3. Set the required `ClassVar` fields:
   - `id` — unique string identifier
   - `name` — display name
   - `description` — short explanation
   - `check_complexity` — `CheckComplexity.SIMPLE` (LAYER 1) or `CheckComplexity.CONFIGURABLE` (LAYER 2)
   - `input_scheme` — list of `CheckFormInput` objects (empty for LAYER 1)
4. Implement `analyze(inputs)` → `CheckResult` and `is_applicable()` → `bool`.

The check is auto-discovered and registered on the next server start.

> *Example custom check — coming soon.*

---

## Using BLG with a Different Front-end

BLG exposes a REST API under `/api/`. Any front-end that can communicate with this API can be used instead of [blg-web](https://github.com/ETolboom/blg-web). The interactive API documentation is available at `http://127.0.0.1:8000/docs` when the server is running.

---

## Configuration and Environment

> *Environment variables, configuration files, and deployment options — coming soon.*

---

## Planned Customization Features

> *The following are planned or under consideration:*

- [ ] Configurable similarity thresholds per check
- [ ] Support for non-English label matching
- [ ] Pluggable parser interface for non-BPMN notations
- [ ] Custom rubric export templates
