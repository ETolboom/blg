from collections import defaultdict
from typing import ClassVar

import spacy
from thefuzz import fuzz

from checks import (
    Check,
    CheckComplexity,
    CheckFormInput,
    CheckResult,
)
from utils import extract_all_tasks, ExtractedTask
from utils.similarity import create_similarity_matrix


class AtomicityCheck(Check):
    id: ClassVar[str] = "atomicity_check"
    name: ClassVar[str] = "Label Atomicity"
    description: ClassVar[str] = "Check the task labels for atomicity"
    check_complexity: ClassVar[CheckComplexity] = CheckComplexity.SIMPLE
    threshold: ClassVar[float] = 0.90
    input_scheme: ClassVar[list[CheckFormInput]] = []

    @classmethod
    def load_dependencies(cls) -> None:
        """Load spacy model required for atomicity checking"""
        load_spacy_model()

    def analyze(self, inputs: list[CheckFormInput] | None = None) -> CheckResult:
        tasks: list[ExtractedTask] = extract_all_tasks(self.model_xml)

        problematic_elements: list[str] = [task.id for task in tasks if atomicity_score(task.name) <= self.threshold]

        return CheckResult(
            id=self.id,
            name=self.name,
            description=self.description,
            check_complexity=self.check_complexity,
            fulfilled=(len(problematic_elements) == 0),
            problematic_elements=problematic_elements,
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
    threshold: ClassVar[float] = 0.90
    input_scheme: ClassVar[list[CheckFormInput]] = []

    def analyze(self, inputs: list[CheckFormInput] | None = None) -> CheckResult:
        tasks: list[ExtractedTask] = extract_all_tasks(self.model_xml)
        if len(tasks) == 0:
            raise Exception("Cannot identify exact duplicates: no tasks found")

        duplicates = find_fuzzy_duplicates(tasks, threshold=self.threshold)

        problematic_elements: list[str] = [t.id for t in duplicates]

        return CheckResult(
            id=self.id,
            name=self.name,
            description=self.description,
            check_complexity=self.check_complexity,
            fulfilled=(len(problematic_elements) == 0),
            problematic_elements=problematic_elements,
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
    threshold: ClassVar[float] = 0.80
    input_scheme: ClassVar[list[CheckFormInput]] = []

    def analyze(self, inputs: list[CheckFormInput] | None = None) -> CheckResult:
        tasks: list[ExtractedTask] = extract_all_tasks(self.model_xml)
        if len(tasks) == 0:
            raise Exception("Cannot identify exact duplicates: no tasks found")

        duplicates: list[ExtractedTask] = find_semantic_duplicates(tasks, threshold=self.threshold)

        problematic_elements: list[str] = [t.id for t in duplicates]

        return CheckResult(
            id=self.id,
            name=self.name,
            description=self.description,
            check_complexity=self.check_complexity,
            fulfilled=(len(problematic_elements) == 0),
            problematic_elements=problematic_elements,
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
    """Returns how atomic a label is. Where 1 means it is fully atomic and describing a single action and 0 being not atomic at all."""
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


def find_semantic_duplicates(
    extracted_tasks: list[ExtractedTask], threshold: float
) -> list[ExtractedTask]:
    labels: list[str] = [t.name for t in extracted_tasks]
    similarity_matrix = create_similarity_matrix(labels, labels, self_similarity=True)

    n = len(labels)
    duplicate_indices: set[int] = set()

    for i in range(n):
        for j in range(i + 1, n):
            score: float = similarity_matrix[i, j].item()
            if score >= threshold:
                duplicate_indices.add(i)
                duplicate_indices.add(j)

    return [extracted_tasks[i] for i in sorted(duplicate_indices)]


def find_fuzzy_duplicates(
    tasks: list[ExtractedTask], threshold: float
) -> list[ExtractedTask]:
    duplicate_indices: set[int] = set()
    threshold_scaled = threshold * 100  # Thefuzz produces values between 0-100

    for i, current_task in enumerate(tasks):
        for j, other_task in enumerate(tasks[i + 1 :], i + 1):
            similarity: int = fuzz.ratio(current_task.name, other_task.name)
            if similarity >= threshold_scaled:
                duplicate_indices.add(i)
                duplicate_indices.add(j)

    return [tasks[i] for i in sorted(duplicate_indices)]
