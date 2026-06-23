This page documents known limitations of BLG's grading engine and gives practical guidance on how to model reference BPMN models and Behavioral Rules to get accurate results.

> **Video walkthrough** — *coming soon.*

---

## Semantic Matching

BLG matches element labels using sentence-embedding cosine similarity (via `sentence-transformers/all-mpnet-base-v2`). This means:

- Small wording variations ("Send invoice" / "Invoice the customer") are usually tolerated.
- Very short or generic labels ("Task 1", "Process", "Do something") may match poorly or ambiguously.
- Language matters — the model performs best on English labels. Non-English labels may match less reliably.

**Recommendation:** use descriptive, domain-specific labels on all BPMN elements.

---

## Distance Constraints

### Default distances

When no followedBy connector is configured, BLG uses ideal distance = 1 and maximum distance = 2. This means BLG allows at most one intermediate BPMN element between two consecutive rule nodes.

### When students add extra steps

If a student's model includes an intermediate step not present in the behavioral rule (e.g. an approval task between two expected tasks), the default maximum distance of 2 may be too small and the second expected element will not be found.

**Solution:** increase the maximum distance on the followedBy connector between the two nodes in the rule.

> *Modeling example — coming soon.*

### When gateways sit between elements

Gateways in the student's model count towards the distance. A sequence `[Task A] → [XOR gateway] → [Task B]` has a distance of 2 between Task A and Task B.

**Solution:** set the ideal distance on the followedBy connector to 2 if a gateway is expected between the two tasks, or set the maximum distance higher to accommodate unexpected gateways.

> *Modeling example — coming soon.*

---

## Boundary Events

Boundary events (timer, message, error, signal, etc.) can be matched in behavioral rules using an Element node. BLG identifies boundary events by type rather than by label:

- A label containing "boundary event" matches any boundary event.
- A label containing the event type (e.g. "message", "timer") matches boundary events of that type.

**Known limitation:** a boundary event that leads to a long sub-process before the next expected element in the rule may exceed the maximum distance.

---

## Multiple Start Nodes

A behavioral rule must have **exactly one start node** — a node with no incoming edges. If the rule graph has multiple start nodes, BLG will raise an error and the criterion will not be evaluated.

**Solution:** ensure the rule has a single entry point. If the process can begin in multiple ways, use an XOR connector at the start or create separate rules in a rule group.

---

## Loops and Cycles

BLG's behavioral rule traversal does not support loops. If the student's BPMN model contains a loop (a path that can be traversed multiple times), BLG evaluates only the first pass.

**Known limitation:** a student who correctly models a retry loop may not receive credit for elements inside the loop if the rule does not account for them explicitly.

---

## Large Parallel Structures

AND branches in a behavioral rule are evaluated independently from the same starting position. This means the order in which elements appear across parallel lanes is not tracked — only that each expected element exists somewhere reachable from the divergence point.

---

## Pool and Lane Checks (LAYER 2)

The Pool-Lane Check uses semantic similarity to match pool and lane names. Very short names (e.g. "HR", "IT") may match unintended pools if the student uses different abbreviations.

**Recommendation:** use full descriptive names for pools and lanes in the reference model and in the check configuration.

---

## Task Coverage (LAYER 1)

Task Coverage compares the labels of all tasks in the student's model against the labels of all tasks in the reference model using semantic similarity. It does not verify task order or placement.

**Known limitation:** if the student duplicates a task (models the same activity twice under different names), Task Coverage may still pass even though one of the duplicates is erroneous.

---

## Behavioral Rules are Not Exhaustive

A behavioral rule only checks the elements it explicitly includes. Elements in the student's model that are not referenced in any rule are not graded (and not penalised). If you want to check the *absence* of a particular element, you need a dedicated LAYER 1 or LAYER 2 check.

---

## Cached Grading Results

Once a submission has been graded, BLG caches the result on disk. If you change the rubric, modify a behavioral rule, or replace the reference model, **you must invalidate the cache** to re-grade existing submissions. The BLG interface does this automatically when the rubric is saved.

---

## Undo in workflows

When working in the workflow editor, CTRL-Z (and similar actions), currently do not have any effect. For now, in case any breaking changes were made, the page can be reloaded such that the last saved state of the workflow can be loaded.
