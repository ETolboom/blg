import torch
from typing import ClassVar

from checks import (
    Check,
    CheckComplexity,
    CheckDetail,
    CheckDetailSection,
    CheckFormInput,
    CheckResult,
    StringFormInput,
)
from utils import extract_all_tasks, ExtractedTask
from utils.similarity import create_similarity_matrix


def _coverage_detail(missing: list[str], unexpected: list[str]) -> CheckDetail | None:
    """Build the info-pop-up breakdown, omitting empty sections."""
    sections = []
    if missing:
        sections.append(
            CheckDetailSection(label="Missing tasks", severity="error", items=missing)
        )
    if unexpected:
        sections.append(
            CheckDetailSection(
                label="Unmatched tasks", severity="warn", items=unexpected
            )
        )
    return CheckDetail(sections=sections) if sections else None


class TaskCoverageCheck(Check):
    id: ClassVar[str] = "task_coverage"
    name: ClassVar[str] = "Task Coverage"
    description: ClassVar[str] = (
        "Checks that the model covers all expected tasks from the reference model"
    )
    check_complexity: ClassVar[CheckComplexity] = CheckComplexity.CONFIGURABLE
    threshold: ClassVar[float] = 0.8
    input_scheme: ClassVar[list[CheckFormInput]] = []
    # Diagnostic sanity gate: never awards points.
    awards_points: ClassVar[bool] = False

    @classmethod
    def load_dependencies(cls) -> None:
        """Load sentence transformer model for semantic similarity"""
        from utils.similarity import load_model

        load_model()

    def analyze(self, inputs: list[CheckFormInput] | None = None) -> CheckResult:
        tasks: list[ExtractedTask] = extract_all_tasks(self.model_xml)

        if inputs is None:
            # Use self.model_xml as the reference — extract task labels and return as inputs
            reference_inputs = [
                StringFormInput(
                    input_label=task.name,
                    data=task.name,
                )
                for task in tasks
                if task.name and task.name.strip()
            ]
            return CheckResult(
                id=self.id,
                name=self.name,
                description=self.description,
                check_complexity=self.check_complexity,
                fulfilled=True,
                problematic_elements=[],
                inputs=reference_inputs,
            )

        # inputs contains one CheckFormInput per reference task (data = task label)
        reference_labels = [
            str(inp.data)
            for inp in inputs
            if isinstance(inp.data, str) and inp.data.strip()
        ]

        if not reference_labels:
            return CheckResult(
                id=self.id,
                name=self.name,
                description=self.description,
                check_complexity=self.check_complexity,
                fulfilled=True,
                confidence=1.0,
                problematic_elements=[],
                inputs=inputs,
            )

        if not tasks:
            # No tasks at all: every expected task is missing — the strongest
            # signal that this submission is better graded manually.
            return CheckResult(
                id=self.id,
                name=self.name,
                description=self.description,
                check_complexity=self.check_complexity,
                fulfilled=False,
                confidence=0.0,
                problematic_elements=[],
                inputs=inputs,
                detail=_coverage_detail(reference_labels, []),
            )

        student_labels = [task.name for task in tasks if task.name]

        # similarity_matrix shape: [len(reference_labels), len(student_labels)]
        similarity_matrix = create_similarity_matrix(
            reference_labels, student_labels, self_similarity=False
        )

        # How many reference tasks are covered by at least one student task?
        best_ref_scores = torch.max(similarity_matrix, dim=1).values
        matched = sum(1 for s in best_ref_scores if s.item() >= self.threshold)
        coverage = matched / len(reference_labels)

        # Expected (reference) tasks that no student task matched well enough.
        missing = [
            label
            for label, score in zip(reference_labels, best_ref_scores)
            if score.item() < self.threshold
        ]

        # Student tasks with no clear reference counterpart are flagged (ids for
        # BPMN highlighting; names for the info pop-up).
        student_best_scores = torch.max(similarity_matrix, dim=0).values
        problematic_elements = [
            task.id
            for task, score in zip(tasks, student_best_scores)
            if task.name and score.item() < self.threshold
        ]
        unexpected = [
            task.name
            for task, score in zip(tasks, student_best_scores)
            if task.name and score.item() < self.threshold
        ]

        # Sanity-gate outcome (3 states):
        #   missing tasks        -> not fulfilled (rules can't match; grade manually)
        #   all present + extras -> indeterminate "?" (needs a human look)
        #   all present, no extra -> fulfilled
        if missing:
            fulfilled: bool | None = False
        elif unexpected:
            fulfilled = None
        else:
            fulfilled = True

        return CheckResult(
            id=self.id,
            name=self.name,
            description=self.description,
            check_complexity=self.check_complexity,
            fulfilled=fulfilled,
            confidence=round(coverage, 3),
            problematic_elements=problematic_elements,
            inputs=inputs,
            detail=_coverage_detail(missing, unexpected),
        )

    def is_applicable(self) -> bool:
        return True
