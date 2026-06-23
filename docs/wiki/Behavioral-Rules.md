Behavioral Rules are the mechanism BLG uses to grade the **flow and ordering** of a student's BPMN model. They make up all LAYER 3 criteria.

---

## What is a Behavioral Rule?

A behavioral rule is a **directed graph of nodes and edges** drawn by the instructor that represents the expected sequence of BPMN elements in a correct solution. When BLG grades a submission it walks the student's BPMN model and attempts to match each node in the rule graph to a real BPMN element.

Matching a node does not by itself award any points. Credit comes only from dedicated **[Points](BPMN-Elements#points)** nodes that you place in the rule graph: a Points node's value is added to the score only when traversal reaches it, which requires every preceding check to have matched. Place a Points node near the end of the flow to award full credit for completing it, or place several at intermediate positions to grant partial credit as the student's model satisfies successive parts of the rule.

---

## Node Types

See [BPMN Elements in Behavioral Rules](BPMN-Elements) for full details on each node type.

| Node type | Represents | Configurable options |
|-----------|-----------|----------------------|
| **Element Check** | A task, event, or data object | Label |
| **Gateway Check** | A BPMN gateway | Type, expected outcomes, optional label and outcome labels |
| **Points** | Credit for an attached check | Points |
| **followedBy** | Distance constraint between two nodes | Ideal distance, maximum distance |
| **AND Connector** | All branches must be satisfied | None |
| **XOR Connector** | At least one branch must be satisfied | None |
| **End** | Optional visual endpoint (ignored during grading) | None |
| **Notes** | Annotation (ignored during grading) | Text |

---

## Edges and Distance

An edge between two nodes in a behavioral rule means "the second element must follow the first". The **followedBy** connector (placed on the edge) refines this by specifying:

- **Ideal distance**: the expected number of BPMN sequence flow edges between the two elements (default: 1, i.e. directly connected).
- **Maximum distance**: the furthest acceptable distance (default: 2).

Elements found beyond the maximum distance are not counted as matches. Elements found between ideal and maximum distance are matched but their BPMN IDs are included in `problematic_elements`.

---

## Branching: AND and XOR

A behavioral rule can express **parallel** or **alternative** paths using connectors:

### AND branches
All branches leaving an AND split must be matched in the student's model. Points from all branches are summed.

```
[Start Task] → [AND split]  → [Branch A] ──┐
                            → [Branch B] ──┤─ AND Connector → [Merge Task]
```

### XOR branches
At least one branch must be matched. BLG tries every branch and selects the best-scoring one.

```
[Decision Task] → [Branch A] ──┐
                → [Branch B] ──┤─ XOR Connector → [Next Task]
```

---

## Matching Logic

1. BLG finds the start node in the rule (the unique node with no incoming edges).
2. It locates the corresponding element in the student's BPMN using semantic similarity.
3. It traverses the rule graph node by node, at each step searching the student's BPMN for the expected element within the configured distance.
4. For each check matched: a [MatchDetail](Glossary#match-score) is recorded and traversal continues to the next node.
5. For each check not found: the element is recorded as problematic and that branch of traversal stops, so any Points nodes further along it are never reached.
6. When traversal reaches a Points node, its configured value is added to the rule's score.

---

## Behavioral Rule Groups

A **Behavioral Rule Group** bundles multiple behavioral rules into a single rubric criterion. The group has a condition that determines how individual rule results are combined:

| Condition | Meaning | Points awarded |
|-----------|---------|----------------|
| **XOR** | At least one rule must be satisfied | Points from the best-performing rule |
| **AND** | All rules must be satisfied | Points from the best rule (only if all pass) |

### When to use groups

- **XOR**: the student can choose one of several valid solutions (e.g. two alternative process designs).
- **AND**: the process has distinct parts that must all be present (e.g. the happy path and the error path as separate rules).

---

## Creating and Editing Rules

Behavioral rules are created and edited in the BLG interface. They are stored as JSON files in the `rules/` directory of the data folder.

> **Clip: Creating a behavioral rule:** *coming soon.*

> **Clip: Creating a rule group:** *coming soon.*

---

## Tips and Limitations

- A rule must have **exactly one start node** (a node with no incoming edges).
- Notes nodes are visual only and have no effect on grading.
- The order in which you draw branches does not matter; BLG tries all paths.
- Very long chains with a small maximum distance may fail to match elements that are separated by intermediate gateways in the student's model; adjust the maximum distance on the followedBy connector if needed.

See [Modeling Considerations](Modeling-Considerations) for more.
