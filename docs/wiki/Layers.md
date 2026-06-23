# The Three Layers

BLG organizes all grading criteria into three layers. The layer of a criterion describes how it works, what it requires from the instructor, and how much modeling detail it can assess.

---

## Overview

| Layer | Name | Configuration required | Depends on reference model? |
|-------|------|------------------------|----------------------------|
| 1 | Quality Checks | None | No |
| 2 | Simple Model-Dependent Checks | Instructor inputs (pools/lanes, task types, …) | Yes |
| 3 | Complex Model-Dependent Checks | Full workflow graph (Behavioral Rule) | Yes |

---

## LAYER 1: Quality Checks (Model-Agnostic)

LAYER 1 criteria assess **general modeling quality** properties that should hold regardless of the assignment. They require no configuration and no reference model; the instructor selects them during onboarding and BLG evaluates them automatically.

### When to use
Use LAYER 1 checks for properties every student model must satisfy, independent of the specific process being modeled.

### Built-in LAYER 1 checks

| Check | What it verifies |
|-------|-----------------|
| **No Deadlocks** | The process can always reach its end state (option to complete) |
| **Dead Activities** | Every activity in the model is reachable |
| **Unique End Event Execution** | There is exactly one unambiguous path to the final end event |
| **Synchronization** | Concurrent activities joined by parallel gateways are correctly synchronized |
| **Label Atomicity** | Task labels describe a single, indivisible action |
| **Exact Duplicate Tasks** | No two tasks share an identical or near-identical label |
| **Semantically Duplicate Tasks** | No two tasks are semantically equivalent |

---

## LAYER 2: Simple Model-Dependent Checks

LAYER 2 criteria check **structural properties** of the student's model against instructor-specified values. Unlike LAYER 1, they require the instructor to configure inputs (e.g. expected pool names, lane names, or task types).

### When to use
Use LAYER 2 checks when you want to verify specific structural facts about the model. For example, that a certain participant appears as a pool, or that certain tasks use the correct BPMN task type.

### Built-in LAYER 2 checks

| Check | Configuration | What it verifies |
|-------|---------------|-----------------|
| **Pool-Lane Check** | Expected pools (keys) and their lanes (values) | Correct pools and lanes are present with the correct names |
| **Task Type** | Expected task label → task type mappings | Tasks are modeled using the correct BPMN task type (user task, service task, etc.) |
| **Task Coverage** | Expected task labels (auto-filled from the reference model) and a similarity threshold | All tasks from the reference model are present in the student's model |

---

## LAYER 3: Complex Model-Dependent Checks

LAYER 3 criteria assess the **behavioral flow** of the student's model using a [Behavioral Rule](Behavioral-Rules), a directed graph of elements, gateways and connectors drawn by the instructor. BLG traverses the student's BPMN, matching each node in turn, and awards credit from the **Points** nodes the traversal reaches.

LAYER 3 is the most expressive layer: it can verify ordering, gateway logic, distance between elements, and alternative or parallel solutions.

### When to use
Use LAYER 3 when you need to check that specific activities occur in a specific order, that certain decisions are modeled as a particular gateway type, or that parallel or alternative paths are present.

### Key concepts
- **Behavioral Rule**: a single workflow graph representing one expected behavior.
- **Behavioral Rule Group**: multiple rules combined with AND (all required) or XOR (any one suffices).
- **Points**: granted only by Points nodes placed in the rule; a Points node is earned when traversal reaches it, so partial credit follows naturally when a student matches the earlier part of a rule but not the rest.

See [Behavioral Rules](Behavioral-Rules) for a detailed explanation.

---

## Adding a Custom Check

New checks can be added for any layer by placing a Python file in `checks/implementations/` and subclassing `Check`. See the developer documentation for details.
