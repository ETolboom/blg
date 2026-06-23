This page documents the key design decisions made in BLG and the rationale behind them.

> This page is intended for developers and instructors who want to understand *why* BLG works the way it does.

---

## Semantic Similarity for Element Matching

**Decision:** BLG matches BPMN element labels using sentence-embedding cosine similarity rather than exact string matching.

**Rationale:** Students rarely use the exact same label as the instructor's reference model. Exact matching would produce too many false negatives (missed matches) for minor wording variations. Sentence embeddings capture semantic meaning, allowing "Send invoice to client" and "Invoice the customer" to match correctly.

**Trade-off:** Semantic matching can produce false positives if labels are semantically similar but represent different activities. The match threshold (0.6 minimum, 0.8 ideal) was chosen to balance recall and precision. Instructors can inspect confidence scores and flagged elements to identify uncertain matches.

---

## Layered Check Architecture

**Decision:** Checks are organized into three layers (model-agnostic, simple model-dependent, complex model-dependent) with a plugin-based implementation system.

**Rationale:** Different assignment types need different grading strategies. A single monolithic grader cannot cover all cases. Separating checks into layers makes it clear to instructors what each check does and what it requires. The plugin architecture allows new checks to be added without modifying core code.

---

## Behavioral Rules as Graphs

**Decision:** LAYER 3 criteria are expressed as directed graphs (behavioral rules) rather than as formal specifications or test cases.

**Rationale:** Instructors are domain experts (e.g. business process modelers), not programmers. A visual graph editor is more accessible than a formal language. Graphs also map naturally onto the structure of BPMN, which itself is a graph of elements and flows.

---

## Points Nodes (Partial Credit)

**Decision:** Behavioral rules carry credit on dedicated **Points** nodes placed in the rule graph, rather than awarding a fixed amount per matched node or all-or-nothing per rule. A Points node is earned only when traversal reaches it.

**Rationale:** A student may correctly model most of a process but miss one step. Awarding zero points for the entire rule would not reflect their partial understanding. Putting points on explicit nodes lets the instructor decide exactly where credit is granted: one node near the end rewards completing the whole flow, while several intermediate nodes hand out proportional credit as successive parts of the rule are satisfied.

---

## Separation of Reference XML from Rubric JSON

**Decision:** The reference BPMN XML is stored in a separate `reference.bpmn` file rather than embedded in `rubric.json`.

**Rationale:** BPMN files can be very large. Embedding them in the rubric JSON would make the rubric file unwieldy, slow to parse, and difficult to version-control. Storing the XML separately also makes it easy to replace the reference model without modifying the rubric structure.

---

## Rule Groups: MAX Scoring

**Decision:** When a Behavioral Rule Group is fulfilled, the points awarded equal the **maximum** points among all member rules (not the sum or average).

**Rationale:** Rules in a group represent alternative or complementary solutions to the same grading criterion. A student who satisfies the best rule should receive the full points for that rule, not a diluted fraction. Summing would double-count; averaging would undervalue a strong solution.

---

## Caching Submission Results

**Decision:** Grading results are cached on disk as `.bpmn.json` files and reused on subsequent requests.

**Rationale:** Grading a submission is computationally expensive: it runs all registered checks, loads ML models, and traverses the BPMN graph. Caching avoids repeating this work every time the instructor views a submission. The cache is invalidated automatically when the rubric changes.

---

## Hybrid Python/Rust Architecture

**Decision:** Control-flow analysis (deadlock detection, dead activities, etc.) reuses an existing Rust library, `rust_bpmn_analyzer` by Tim Kräuter, exposed to Python through the `rust_bpmn_analyzer_bindings` package.

**Rationale:** A capable implementation of this analysis already existed in Rust, so rather than reimplement exhaustive state-space exploration in Python, BLG simply wraps it. The choice of Rust was the upstream library's, not BLG's; BLG's contribution is the Python bindings that let the rest of the (Python) codebase call into it.
