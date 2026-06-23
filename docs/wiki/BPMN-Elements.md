# BPMN Elements in Behavioral Rules

This page describes each node type available when building a [Behavioral Rule](Behavioral-Rules) and how BLG uses them during grading.

> **Video walkthrough:** *coming soon.*

---

## Element Check

An **Element Check** node represents a BPMN task, intermediate event, or data object that must appear in the student's model at this point in the process.

### Configuration

| Field | Description | Default |
|-------|-------------|---------|
| **Label** | The name of the expected BPMN element | *(required)* |

To grant points, attach [Points](#points) node to award credit when this element is matched.

### How it is matched

BLG searches the student's BPMN starting from the current position and traversing up to the configured maximum distance. Matching uses **semantic similarity** (sentence embeddings), so minor wording differences (e.g. "Send invoice" vs "Invoice customer") are tolerated.

| Match score | Outcome |
|-------------|---------|
| ≥ 0.8 | Ideal match: full points, not flagged |
| ≥ 0.6 and < 0.8 | Acceptable match: full points, element flagged as problematic |
| < 0.6 | No match: zero points, element flagged |

### Supported BPMN element types

- Tasks of any type (user task, service task, script task, manual task, etc.)
- Start and end events
- Intermediate catch and throw events (timer, message, error, signal, …)
- Boundary events: matched by event type (e.g. "message boundary event")
- Data objects and data stores

---

## Gateway Check

A **Gateway Check** node represents a BPMN gateway (a decision or fork/join point) that must appear in the student's model.

### Configuration

| Field | Description | Default |
|-------|-------------|---------|
| **Type** | Gateway type: XOR, AND, OR, event-based, or complex | *(required)* |
| **Expected outcomes** | Number of outgoing branches | *(required)* |
| **Gateway label** | Expected label on the gateway element | None |
| **Check gateway label** | Whether to verify the gateway label | false |
| **Outcome labels** | Expected labels on the outgoing sequence flows | None |
| **Check outcome labels** | Whether to verify the outcome labels | false |

As with the Element Check, points are awarded via an attached [Points](#points) node rather than configured on the gateway node itself.

### Gateway type mapping

| BLG type name | BPMN gateway |
|---------------|-------------|
| XOR / exclusive | Exclusive (data-based) gateway |
| AND / parallel | Parallel gateway |
| OR / inclusive | Inclusive gateway |
| event / event-based | Event-based gateway |
| complex | Complex gateway |

### How it is matched

BLG looks for a gateway of the correct type with the correct number of outgoing branches within the configured distance. If label checking is enabled, the gateway's label and/or its outgoing flow labels are compared against the configured values using semantic similarity.

---

## Points

A **Points** node assigns the credit awarded for a matched check. Rather than carrying points on the Element Check or Gateway Check itself, you attach a Points node to a check (or connector), keeping the points value separate from the element it rewards.

### Configuration

| Field | Description | Default |
|-------|-------------|---------|
| **Points** | Value added to the rule's score when traversal reaches this node | 0 |

A Points node's value is added to the rule's score only when traversal reaches it, which requires the checks before it to have matched. A rule's total is therefore the sum of the Points nodes the traversal reaches. Place one near the end to reward completing the whole flow, or several at intermediate positions for fine-grained, proportional partial credit (see [Design Choices](Design-Choices)).

---

## followedBy

A **followedBy** connector is placed on an edge between two nodes to specify distance constraints. It is not itself matched to a BPMN element.

### Configuration

| Field | Description | Default |
|-------|-------------|---------|
| **Ideal distance** | Expected number of BPMN edges between the two elements | 1 |
| **Maximum distance** | Furthest acceptable number of BPMN edges | 2 |

When no followedBy is present on an edge, BLG uses the defaults (ideal: 1, max: 2).

**Example:** if a student model has an intermediate task between the two expected elements, setting `max_distance = 2` allows BLG to still find the second element rather than failing.

---

## AND Connector

An **AND Connector** node marks the point where parallel branches converge. All incoming branches must successfully reach the connector for the traversal to continue past it.

- Has no points of its own.
- Is paired with a divergence point (a node with multiple outgoing edges) elsewhere in the rule.

---

## XOR Connector

An **XOR Connector** node marks the point where alternative branches converge. At least one incoming branch must successfully reach the connector; BLG selects the best-scoring branch.

- Has no points of its own.
- Is paired with a divergence point elsewhere in the rule.

---

## End

An **End** node is an optional visual marker for where a path through the rule is meant to finish. Like the Notes node, it has **no effect on grading**: it is not matched to a BPMN element and carries no points. During evaluation BLG takes the rule's start to be the node with no incoming edges and traverses forward until a path runs out of successors; it does not consult End nodes. Use one only to make a rule's intended endpoint clearer to readers.

---

## Notes

A **Notes** node is a visual annotation. It has a text field and can be connected to any other node for clarity, but is **completely ignored during grading**. Use it to add comments or reminders to a rule without affecting evaluation.

---

## Example: Simple Sequential Rule

```
[Register order] ──followedBy──> [Check stock] ──followedBy──> [Ship order]
      (1 pt)       ideal=1, max=2       (1 pt)    ideal=1, max=2     (1 pt)
```

BLG finds "Register order" in the student's model, then looks within 2 steps for "Check stock", then within 2 more steps for "Ship order". Up to 3 points can be awarded.

---

## Example: Gateway with Branches

> *Diagram coming soon.*

<!-- Describe an XOR gateway with two outcome branches, each with one element node, converging at an XOR connector. -->

---

## Example: Parallel Paths

> *Diagram coming soon.*

<!-- Describe a parallel split with two branches of element nodes, converging at an AND connector. -->
