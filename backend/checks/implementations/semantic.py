from typing import ClassVar

import spacy
from thefuzz import fuzz

from checks import (
    Check,
    CheckComplexity,
    CheckDetail,
    CheckDetailSection,
    CheckFormInput,
    CheckResult,
)
from utils import extract_all_tasks, ExtractedTask
from utils.similarity import create_similarity_matrix


# A candidate duplicate: the two tasks plus a 0..1 confidence score.
DuplicatePair = tuple[ExtractedTask, ExtractedTask, float]

_DUP_MIN_LABEL = "Flag candidates from"
_DUP_IDEAL_LABEL = "Count as duplicate at"
_DUP_HINT = (
    "Pairs at least this similar are surfaced as possible duplicates; at or above "
    "the upper value they're counted as a definite duplicate (failing the check). "
    "Lowering the floor surfaces more candidates to review."
)


def _format_pair(pair: DuplicatePair) -> str:
    a, b, score = pair
    return f"{a.name} ↔ {b.name} ({round(score * 100)}% confident)"


def _duplicate_result(
    pairs: list[DuplicatePair], ideal_threshold: float
) -> tuple[list[str], CheckDetail | None, bool | None]:
    """Turn candidate duplicate pairs into (flagged element ids, info-pop-up
    breakdown, fulfilled). Like Task Coverage, this is a 3-state sanity outcome:

    - no candidate pairs                 -> fulfilled (no duplicates)
    - a pair at/above the ideal threshold -> not fulfilled (a confident duplicate)
    - only below-ideal pairs              -> indeterminate "?" (needs a human look)
    """
    flagged: list[str] = []
    for a, b, _ in pairs:
        for task in (a, b):
            if task.id not in flagged:
                flagged.append(task.id)

    likely = [p for p in pairs if p[2] >= ideal_threshold]
    possible = [p for p in pairs if p[2] < ideal_threshold]

    sections: list[CheckDetailSection] = []
    if likely:
        sections.append(
            CheckDetailSection(
                label="Likely duplicates",
                severity="error",
                items=[_format_pair(p) for p in likely],
            )
        )
    if possible:
        sections.append(
            CheckDetailSection(
                label="Possible duplicates",
                severity="warn",
                items=[_format_pair(p) for p in possible],
            )
        )
    detail = CheckDetail(sections=sections) if sections else None

    if likely:
        fulfilled: bool | None = False
    elif possible:
        fulfilled = None
    else:
        fulfilled = True

    return flagged, detail, fulfilled


class AtomicityCheck(Check):
    id: ClassVar[str] = "atomicity_check"
    name: ClassVar[str] = "Label Atomicity"
    description: ClassVar[str] = "Check the task labels for atomicity"
    check_complexity: ClassVar[CheckComplexity] = CheckComplexity.SIMPLE
    threshold: ClassVar[float] = 0.90
    supports_threshold_override: ClassVar[bool] = True
    threshold_label: ClassVar[str] = "Minimum atomicity to pass"
    threshold_hint: ClassVar[str | None] = (
        "Labels scoring at or below this are flagged as non-atomic. "
        "Lower it to be more lenient."
    )
    input_scheme: ClassVar[list[CheckFormInput]] = []

    @classmethod
    def load_dependencies(cls) -> None:
        """Load spacy model required for atomicity checking"""
        load_spacy_model()

    def analyze(
        self,
        inputs: list[CheckFormInput] | None = None,
        threshold: float | None = None,
        ideal_threshold: float | None = None,
    ) -> CheckResult:
        effective_threshold = threshold if threshold is not None else self.threshold
        tasks: list[ExtractedTask] = extract_all_tasks(self.model_xml)

        scored = [(task, atomicity_score(task.name)) for task in tasks]
        flagged = [
            (task, score) for task, score in scored if score <= effective_threshold
        ]

        problematic_elements: list[str] = [task.id for task, _ in flagged]

        detail = None
        if flagged:
            detail = CheckDetail(
                sections=[
                    CheckDetailSection(
                        label="Non-atomic labels",
                        severity="warn",
                        items=[
                            f"{task.name} ({round(score * 100)}% atomic)"
                            for task, score in flagged
                        ],
                    )
                ]
            )

        return CheckResult(
            id=self.id,
            name=self.name,
            description=self.description,
            check_complexity=self.check_complexity,
            fulfilled=(len(problematic_elements) == 0),
            problematic_elements=problematic_elements,
            detail=detail,
        )

    def is_applicable(self) -> bool:
        return True


class ExactDuplicateTasks(Check):
    id: ClassVar[str] = "exact_duplicate_tasks"
    name: ClassVar[str] = "Exact Duplicate Tasks"
    description: ClassVar[str] = (
        "Check the model for any duplicate tasks based on fuzzy matching"
    )
    check_complexity: ClassVar[CheckComplexity] = CheckComplexity.SIMPLE
    # Minimum similarity to count as a candidate; at/above ideal it's a confident
    # duplicate (below ideal -> indeterminate "?").
    threshold: ClassVar[float] = 0.90
    ideal_threshold: ClassVar[float] = 0.95
    supports_threshold_override: ClassVar[bool] = True
    threshold_label: ClassVar[str] = _DUP_MIN_LABEL
    ideal_threshold_label: ClassVar[str | None] = _DUP_IDEAL_LABEL
    threshold_hint: ClassVar[str | None] = _DUP_HINT
    input_scheme: ClassVar[list[CheckFormInput]] = []

    def analyze(
        self,
        inputs: list[CheckFormInput] | None = None,
        threshold: float | None = None,
        ideal_threshold: float | None = None,
    ) -> CheckResult:
        effective_threshold = threshold if threshold is not None else self.threshold
        effective_ideal = (
            ideal_threshold if ideal_threshold is not None else self.ideal_threshold
        )
        tasks: list[ExtractedTask] = extract_all_tasks(self.model_xml)
        if len(tasks) == 0:
            raise Exception("Cannot identify exact duplicates: no tasks found")

        pairs = find_fuzzy_duplicate_pairs(tasks, threshold=effective_threshold)
        problematic_elements, detail, fulfilled = _duplicate_result(
            pairs, effective_ideal
        )

        return CheckResult(
            id=self.id,
            name=self.name,
            description=self.description,
            check_complexity=self.check_complexity,
            fulfilled=fulfilled,
            problematic_elements=problematic_elements,
            detail=detail,
        )

    def is_applicable(self) -> bool:
        return True


class SemanticDuplicateTasks(Check):
    id: ClassVar[str] = "semantic_duplicate_tasks"
    name: ClassVar[str] = "Semantically Duplicate Tasks"
    description: ClassVar[str] = (
        "Check the model for any duplicate tasks based on semantic matching"
    )
    check_complexity: ClassVar[CheckComplexity] = CheckComplexity.SIMPLE
    # Minimum similarity to count as a candidate; at/above ideal it's a confident
    # duplicate (below ideal -> indeterminate "?").
    threshold: ClassVar[float] = 0.80
    ideal_threshold: ClassVar[float] = 0.90
    supports_threshold_override: ClassVar[bool] = True
    threshold_label: ClassVar[str] = _DUP_MIN_LABEL
    ideal_threshold_label: ClassVar[str | None] = _DUP_IDEAL_LABEL
    threshold_hint: ClassVar[str | None] = _DUP_HINT
    input_scheme: ClassVar[list[CheckFormInput]] = []

    def analyze(
        self,
        inputs: list[CheckFormInput] | None = None,
        threshold: float | None = None,
        ideal_threshold: float | None = None,
    ) -> CheckResult:
        effective_threshold = threshold if threshold is not None else self.threshold
        effective_ideal = (
            ideal_threshold if ideal_threshold is not None else self.ideal_threshold
        )
        tasks: list[ExtractedTask] = extract_all_tasks(self.model_xml)
        if len(tasks) == 0:
            raise Exception("Cannot identify semantic duplicates: no tasks found")

        pairs = find_semantic_duplicate_pairs(tasks, threshold=effective_threshold)
        problematic_elements, detail, fulfilled = _duplicate_result(
            pairs, effective_ideal
        )

        return CheckResult(
            id=self.id,
            name=self.name,
            description=self.description,
            check_complexity=self.check_complexity,
            fulfilled=fulfilled,
            problematic_elements=problematic_elements,
            detail=detail,
        )

    def is_applicable(self) -> bool:
        return True


# Helpers

_nlp: spacy.language.Language | None = None


def load_spacy_model() -> None:
    """Load the spacy model. Must be called before using semantic checks."""
    global _nlp
    if _nlp is None:
        print("Loading spacy model...")
        _nlp = spacy.load("en_core_web_md")
        print("Spacy model loaded successfully")


def _get_nlp() -> spacy.language.Language:
    """Get the loaded spacy model, raising an error if not loaded."""
    if _nlp is None:
        raise RuntimeError("Spacy model not loaded. Call load_spacy_model() first.")
    return _nlp


def atomicity_score(label: str) -> float:
    """Returns how atomic a label is. Where 1 means it is fully atomic and
    describing a single action and 0 being not atomic at all."""
    doc = _get_nlp()(label)
    words = label.split()
    conjunction_words = ["and", "or", "then", "after", "also"]

    penalties: float = 0.0
    penalties += len(words) * 0.1
    penalties += sum(1 for word in words if word.lower() in conjunction_words) * 2.0

    # Penalize extra verbs beyond the first. Exclude participles used as
    # adjective/relative-clause modifiers (e.g. "missing" in "receive missing
    # ingredients") which spaCy sometimes mis-tags as VERB.
    verbs = [t for t in doc if t.pos_ == "VERB" and t.dep_ not in ("amod", "acl")]
    penalties += max(0, len(verbs) - 1) * 1.5

    penalties /= 10  # Scale back to 0-1

    return max(0.0, 1.0 - penalties)


def find_semantic_duplicate_pairs(
    extracted_tasks: list[ExtractedTask], threshold: float
) -> list[DuplicatePair]:
    labels: list[str] = [t.name for t in extracted_tasks]
    similarity_matrix = create_similarity_matrix(labels, labels, self_similarity=True)

    n = len(labels)
    pairs: list[DuplicatePair] = []

    for i in range(n):
        for j in range(i + 1, n):
            score: float = similarity_matrix[i, j].item()
            if score >= threshold:
                pairs.append((extracted_tasks[i], extracted_tasks[j], score))

    return pairs


def find_fuzzy_duplicate_pairs(
    tasks: list[ExtractedTask], threshold: float
) -> list[DuplicatePair]:
    pairs: list[DuplicatePair] = []
    threshold_scaled = threshold * 100  # Thefuzz produces values between 0-100

    for i, current_task in enumerate(tasks):
        for j, other_task in enumerate(tasks[i + 1 :], i + 1):
            similarity: int = fuzz.ratio(current_task.name, other_task.name)
            if similarity >= threshold_scaled:
                # Normalise the 0-100 fuzz ratio to a 0-1 confidence.
                pairs.append((current_task, other_task, similarity / 100))

    return pairs
