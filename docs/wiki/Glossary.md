Definitions for all terms used in BLG. Terms are listed alphabetically.

---

## A

### AND Connector
A node used inside a [Behavioral Rule](#behavioral-rule) to express that **all** incoming branches must be satisfied before grading continues. An AND connector corresponds to a parallel split/join in BPMN. Compare with [XOR Connector](#xor-connector).

### AND Condition (Rule Group)
When a [Behavioral Rule Group](#behavioral-rule-group) uses the AND condition, **every** rule in the group must be satisfied for the group criterion to be fulfilled. The points awarded equal the maximum points of the highest-scoring member rule (provided all rules pass). Compare with [XOR Condition](#xor-condition-rule-group).

### Assignment
The combination of a [Reference BPMN Model](#reference-bpmn-model) and an optional [Supplement](#supplement) that defines what students are expected to model.

---

## B

### Behavioral Rule
A directed graph of [nodes](BPMN-Elements) and edges that describes the expected flow of a BPMN process. Each node represents either a BPMN element (task, event, data object) or a gateway, and each edge expresses a "followed by" relationship. BLG traverses a student's BPMN model and awards [points](#points) for each node that is correctly matched.

A behavioral rule is the primary tool for checking model-specific behavior (LAYER 3). It is stored as a JSON file and can be created and edited in the BLG interface.

See [Behavioral Rules](Behavioral-Rules) for a full explanation.

### Behavioral Rule Group
A named collection of [Behavioral Rules](#behavioral-rule) evaluated together as a single [criterion](#criterion--check) in the [rubric](#rubric). A group uses either an [AND](#and-condition-rule-group) or [XOR](#xor-condition-rule-group) condition to determine how individual rule results are aggregated.

Use groups when a student may correctly solve a problem in more than one way (XOR), or when a problem has several distinct required parts (AND).

---

## C

### Check
See [Criterion](#criterion--check).

### Confidence
A value between 0.0 and 1.0 that reflects how closely the student's BPMN model matched the expected elements in a criterion. A confidence of 1.0 means every matched element was an exact or near-exact match; lower values indicate weaker or partial matches.

Confidence is distinct from whether a criterion is *fulfilled*: a criterion can be fulfilled with imperfect confidence, and the confidence score provides nuance for the instructor.

### Criterion / Check
A single grading unit in the [rubric](#rubric). Each criterion corresponds to one [implementation](#implementation) (e.g. "No Deadlocks", "Pool-Lane Check", "Behavioral Rule"). A criterion carries:

- A **name** and **description** visible to the instructor.
- A **layer** (1, 2, or 3) that describes how complex its configuration is.
- A set of **inputs** (for configurable criteria).
- A **default points** value.
- A **fulfilled** flag and **confidence** score, populated after grading.

The words *criterion* and *check* are interchangeable in BLG.

---

## D

### Default Points
The number of points a student receives when a criterion is **fulfilled**. This value is set per criterion in the rubric and defaults to 1.0.

### Distance
In the context of [Behavioral Rules](#behavioral-rule), the distance between two matched elements is the number of BPMN flow edges that separate them in the student's model. Each node in a behavioral rule defines an *ideal distance* and a *maximum distance*:

- **Ideal distance**: the expected number of edges (default: 1). Elements found at the ideal distance receive full credit.
- **Maximum distance**: the furthest acceptable distance (default: 2). Elements found beyond the maximum distance are not matched.

Elements found between the ideal and maximum distance are still matched but flagged as suboptimal and their BPMN element IDs are included in `problematic_elements`.

---

## E

### Element Check (Behavioral Rule Node)
A node type used in a [Behavioral Rule](#behavioral-rule) to represent a BPMN task, event, or data object that must appear in the student's model. When BLG evaluates a rule, it searches for the expected element starting from the current position and traversing the student's model up to the configured maximum distance.

Informally shortened to *Element*. See [BPMN Elements in Behavioral Rules](BPMN-Elements).

---

## F

### followedBy (Connector)
A special edge type in a [Behavioral Rule](#behavioral-rule) that sets the *distance constraints* between the source node and the next element or gateway node. It carries:

- **Ideal distance**: how many BPMN edges should ideally separate the two elements.
- **Maximum distance**: the furthest distance still considered a valid match.

When no followedBy connector is present, BLG uses the defaults (ideal: 1, max: 2).

### Fulfilled
A boolean flag on a [criterion](#criterion--check) that indicates whether the grading condition for that criterion was met in the student's submission. A fulfilled criterion awards its configured [points](#points); an unfulfilled one awards zero.

---

## G

### Gateway Check (Behavioral Rule Node)
A node type used in a [Behavioral Rule](#behavioral-rule) to represent a BPMN gateway (exclusive, parallel, inclusive, event-based, or complex) that must appear at a specific point in the student's model. A gateway node carries additional configuration:

- **Type**: XOR, AND, OR, event-based, or complex.
- **Expected outcomes**: the number of outgoing paths.
- **Gateway label** *(optional)*: checked if "check gateway label" is enabled.
- **Outcome labels** *(optional)*: labels on the outgoing flows, checked if "check outcome labels" is enabled.

Informally shortened to *Gateway*. See [BPMN Elements in Behavioral Rules](BPMN-Elements).

### Gateway Outcomes
The expected number of outgoing branches from a [gateway node](#gateway-check-behavioral-rule-node) in a behavioral rule. BLG verifies that the matched gateway in the student's model has exactly this many outgoing edges.

---

## I

### Implementation
The code that performs the analysis for a [criterion](#criterion--check). BLG ships with several built-in implementations (no deadlocks, task coverage, label atomicity, etc.) and supports adding new ones by placing a Python file in `checks/implementations/`.

Each implementation declares its layer, name, description, and accepted inputs.

---

## L

### Lane
A subdivision of a [Pool](#pool) that represents a role or resource group responsible for a set of activities. BLG can check that the correct lanes exist with the correct names using the Pool-Lane Check (LAYER 2).

### LAYER 1: Quality Checks (Model-Agnostic)
Criteria that are evaluated **without** a reference BPMN model. They assess general modeling quality properties that should hold regardless of what the process models. For example, the absence of deadlocks or semantically duplicate task labels. LAYER 1 criteria require no configuration input from the instructor.

Built-in LAYER 1 checks:
| Check | Description |
|-------|-------------|
| No Deadlocks | The process can always reach its end state |
| Dead Activities | All activities are reachable |
| Unique End Event Execution | There is exactly one unambiguous path to the end event |
| Synchronization | Concurrent activities are properly synchronized |
| Label Atomicity | Task labels express a single action |
| Exact Duplicate Tasks | No tasks share an identical or near-identical label |
| Semantically Duplicate Tasks | No tasks share a semantically equivalent label |

### LAYER 2: Simple Model-Dependent Checks
Criteria that require **configuration inputs** from the instructor but do not involve a full workflow graph. They check structural properties of the student's model against instructor-specified values. For example, verifying that specific pools and lanes are present with correct names, or that tasks are of the correct BPMN type.

Built-in LAYER 2 checks:
| Check | Description |
|-------|-------------|
| Pool-Lane Check | Verifies expected pools and lanes by name |
| Task Type | Verifies that tasks use the correct BPMN task type (user task, service task, etc.) |
| Task Coverage | Checks that all expected tasks from the reference model are present (non-scoring diagnostic gate) |

### LAYER 3: Complex Model-Dependent Checks
Criteria that evaluate the **behavioral flow** of the student's model against a graph of expected elements and transitions. These are always [Behavioral Rules](#behavioral-rule) (or [Behavioral Rule Groups](#behavioral-rule-group)) and can capture ordering, gateway logic, and distance constraints.

---

## M

### Match Score
A value between 0.0 and 1.0 reflecting the semantic similarity between a workflow node's label and the label of the matched BPMN element in the student's model. BLG uses sentence-embedding cosine similarity to compute match scores:

- **≥ 0.8**: ideal match (full credit, no flag).
- **≥ 0.6 and < 0.8**: acceptable match (credit awarded but element flagged as suboptimal).
- **< 0.6**: no match (element not found).

---

## N

### Notes Node
A visual annotation node in a [Behavioral Rule](#behavioral-rule) that carries a text comment. Notes nodes are ignored during grading and have no effect on the evaluation.

---

## P

### Points
The numerical value awarded to a student for a [criterion](#criterion--check). Points are always non-negative. The full amount (the *default points* configured in the rubric) is awarded when the criterion is fulfilled; partial points may be awarded by [Behavioral Rules](#behavioral-rule) depending on how many nodes were successfully matched.

The word *points* is used consistently throughout BLG. Avoid using "score" or "grade" to refer to this value.

### Pool
The top-level container element in a BPMN model, typically representing a participant or organization. A BPMN model may contain multiple pools. BLG's Pool-Lane Check (LAYER 2) can verify that the expected pools and their lanes are present in the student's model.

### Problematic Elements
A list of BPMN element IDs flagged during grading of a criterion. An element is flagged when:
- Its match score was below the ideal threshold (0.8) but above the minimum threshold (0.6), or
- It was found at a distance greater than the ideal distance.

Problematic elements are highlighted in the BLG interface to help instructors give targeted feedback.

---

## R

### Reference BPMN Model
The instructor's BPMN model that represents a correct (or reference) solution to the assignment. It is used by LAYER 2 and LAYER 3 checks as the ground truth against which student submissions are compared. The reference model is stored separately from the rubric and is not included in graded exports.

### Rubric
The complete set of [criteria](#criterion--check) used to grade an assignment. Each criterion in the rubric specifies:

- Which [implementation](#implementation) performs the grading.
- Configuration inputs (for LAYER 2 checks).
- Default points.

The rubric is shared across all student [submissions](#submission) for an assignment. Changing the rubric invalidates previously cached grading results.

---

## S

### Submission
A student's BPMN model file (`.bpmn`) uploaded to BLG for grading. Each submission is graded against the [rubric](#rubric) and produces a set of [criterion](#criterion--check) results. Results are cached on disk and reused unless the rubric changes.

### Supplement
An optional PDF document attached to an [assignment](#assignment) that students can view alongside the reference model. Typically used for assignment descriptions, textual process narratives, or constraints that are difficult to express in the reference BPMN.

---

## W

### Workflow (Behavioral Rule)
The directed graph of nodes and edges that makes up a [Behavioral Rule](#behavioral-rule). A workflow begins with a single start node (an element or gateway with no incoming edges) and continues until all paths have been traversed. BLG evaluates a student's BPMN by walking this workflow and matching each node to a BPMN element.

---

## X

### XOR Connector
A node used inside a [Behavioral Rule](#behavioral-rule) to express that **at least one** incoming branch must be satisfied before grading continues. An XOR connector corresponds to an exclusive decision point. Compare with [AND Connector](#and-connector).

### XOR Condition (Rule Group)
When a [Behavioral Rule Group](#behavioral-rule-group) uses the XOR condition, **at least one** rule in the group must be satisfied. The points awarded equal those of the best-performing rule. Use XOR when students may produce alternative but equally valid solutions.
