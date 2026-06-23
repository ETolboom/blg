This page documents the key design decisions made in BLG and the rationale behind them.

> This page is intended for developers and instructors who want to understand *why* BLG works the way it does.

---

## Semantic Similarity for Element Matching

**Decision:** BLG matches BPMN element labels using sentence-embedding cosine similarity rather than exact string matching.

**Rationale:** Students rarely use the exact same label as the instructor's reference model. Exact matching would produce too many false negatives (missed matches) for minor wording variations. Sentence embeddings capture semantic meaning, allowing "Send invoice to client" and "Invoice the customer" to match correctly.

**Trade-off:** Semantic matching can produce false positives if labels are semantically similar but represent different activities. The match threshold (0.6 minimum, 0.8 ideal) was chosen to balance recall and precision. Instructors can inspect confidence scores and flagged elements to identify uncertain matches.

---

## Layered Check Architecture

**Decision:** Checks are organised into three layers (model-agnostic, simple model-dependent, complex model-dependent) with a plugin-based implementation system.

**Rationale:** Different assignment types need different grading strategies. A single monolithic grader cannot cover all cases. Separating checks into layers makes it clear to instructors what each check does and what it requires. The plugin architecture allows new checks to be added without modifying core code.

---

## Behavioral Rules as Graphs

**Decision:** LAYER 3 criteria are expressed as directed graphs (behavioral rules) rather than as formal specifications or test cases.

**Rationale:** Instructors are domain experts (e.g. business process modelers), not programmers. A visual graph editor is more accessible than a formal language. Graphs also map naturally onto the structure of BPMN, which itself is a graph of elements and flows.

---

## Points Per Node (Partial Credit)

**Decision:** Behavioral rules award points per matched node rather than all-or-nothing per rule.

**Rationale:** A student may correctly model most of a process but miss one step. Awarding zero points for the entire rule would not reflect their partial understanding. Per-node points allow fine-grained, proportional credit.

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

**Rationale:** Grading a submission is computationally expensive — it runs all registered checks, loads ML models, and traverses the BPMN graph. Caching avoids repeating this work every time the instructor views a submission. The cache is invalidated automatically when the rubric changes.

---

## Hybrid Python/Rust Architecture

**Decision:** Control-flow analysis (deadlock detection, dead activities, etc.) is implemented in Rust and exposed to Python via PyO3/maturin.

**Rationale:** Control-flow analysis requires exhaustive state-space exploration, which is computationally intensive. Rust provides the performance needed to analyse non-trivial BPMN models in acceptable time. All other logic remains in Python for ease of development and extension.

---

## Items to document

> *The following topics are not yet covered on this page and should be added:*

- [ ] Choice of `sentence-transformers/all-mpnet-base-v2` model
- [ ] Decision to use FastAPI over other Python web frameworks
- [ ] Front-end technology choices (blg-web)
- [ ] Data directory layout rationale
- [ ] XOR vs AND connector evaluation order
