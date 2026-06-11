import io

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from pydantic import BaseModel

from checks import CheckComplexity, CheckDetail, CheckFormInput, CheckResult
from rules.manager import RuleEvaluationSummary


class Assignment(BaseModel):
    # Set default value in case we want to onboard without a reference model
    reference_xml: str | None = ""


class GroupResultSummary(BaseModel):
    best_rule_id: str | None = None
    earned_points: float = 0.0
    rule_results: list[RuleEvaluationSummary] = []


class SubmissionCriterionResult(BaseModel):
    id: str
    score: float | None = None
    fulfilled: bool | None = None
    confidence: float = 0.0
    problematic_elements: list[str] = []
    inputs: list[CheckFormInput] = []
    group_result: GroupResultSummary | None = None
    detail: CheckDetail | None = None
    threshold_override: float | None = None
    ideal_threshold_override: float | None = None
    notes: str | None = None


class SubmissionResult(BaseModel):
    criteria: list[SubmissionCriterionResult] = []


class RubricCriterion(CheckResult):
    fulfilled: bool | None = None
    score: float | None = None
    default_points: float = 1.0
    group_result: GroupResultSummary | None = None
    supports_threshold: bool = False
    default_threshold: float | None = None
    default_ideal_threshold: float | None = None
    threshold_override: float | None = None
    ideal_threshold_override: float | None = None
    notes: str | None = None
    threshold_label: str | None = None
    ideal_threshold_label: str | None = None
    threshold_hint: str | None = None


class CriterionDefinition(BaseModel):
    id: str
    name: str
    check_complexity: CheckComplexity
    description: str = ""
    default_points: float = 1.0
    inputs: list[CheckFormInput] = []
    supports_threshold: bool = False
    default_threshold: float | None = None
    default_ideal_threshold: float | None = None


class RubricDefinition(BaseModel):
    criteria: list[CriterionDefinition]
    assignment: Assignment | None = None

    def to_disk_json(self) -> str:
        """Serialize the rubric definition, excluding the reference XML."""
        return self.model_dump_json(exclude={"assignment": {"reference_xml"}})


class OnboardingRubric(BaseModel):
    assignment: Assignment
    checks: list[str] = []


class Rubric(BaseModel):
    criteria: list[RubricCriterion]
    assignment: Assignment | None

    def to_disk_json(self) -> str:
        """Serialize the rubric to JSON, excluding the reference XML."""
        return self.model_dump_json(exclude={"assignment": {"reference_xml"}})

    def to_excel_worksheet(self, workbook: Workbook, filename: str) -> None:
        """Write rubric criteria and scores as a formatted worksheet in the given workbook."""
        worksheet = workbook.create_sheet(filename)

        # Define styles
        header_font = Font(bold=True, color="FFFFFF", size=12)
        header_fill = PatternFill(
            start_color="2E75B6", end_color="2E75B6", fill_type="solid"
        )
        criterion_font = Font(bold=True, size=11)
        criterion_fill = PatternFill(
            start_color="E8F1FF", end_color="E8F1FF", fill_type="solid"
        )
        border = Border(
            left=Side(border_style="thin", color="CCCCCC"),
            right=Side(border_style="thin", color="CCCCCC"),
            top=Side(border_style="thin", color="CCCCCC"),
            bottom=Side(border_style="thin", color="CCCCCC"),
        )
        wrap_alignment = Alignment(wrap_text=True, vertical="top")
        center_alignment = Alignment(horizontal="center", vertical="center")

        # Add headers
        headers = ["Criterion", "Description", "Points", "Threshold", "Notes"]
        for col, header in enumerate(headers, 1):
            cell = worksheet.cell(row=1, column=col, value=header)
            cell.font = header_font
            cell.fill = header_fill
            cell.border = border
            cell.alignment = center_alignment

        def calculate_points(criterion):
            if not criterion.fulfilled:
                return 0.0
            elif criterion.score is not None:
                return max(0.0, criterion.score)
            else:
                return max(0.0, criterion.default_points)

        def _line(label, override, default) -> str | None:
            """One threshold line, annotating the default when it was overridden."""
            if override is not None:
                return f"{label} {override} (default {default})"
            if default is not None:
                return f"{label} {default}"
            return None

        def threshold_cell(criterion) -> str:
            """Make the deviation traceable: show the effective minimum (and ideal,
            where the check has one) cut-offs, annotating any override."""
            if not criterion.supports_threshold:
                return ""
            lines = [
                _line("min", criterion.threshold_override, criterion.default_threshold),
                _line(
                    "ideal",
                    criterion.ideal_threshold_override,
                    criterion.default_ideal_threshold,
                ),
            ]
            return "\n".join(line for line in lines if line)

        # Add criteria data
        current_row = 2
        for criterion in self.criteria:
            points = calculate_points(criterion)

            worksheet.cell(row=current_row, column=1, value=criterion.name)
            worksheet.cell(row=current_row, column=2, value=criterion.description)
            worksheet.cell(row=current_row, column=3, value=points)
            worksheet.cell(row=current_row, column=4, value=threshold_cell(criterion))
            worksheet.cell(row=current_row, column=5, value=criterion.notes or "")

            # Apply styling
            for col in range(1, 6):
                cell = worksheet.cell(row=current_row, column=col)
                cell.border = border
                cell.font = criterion_font
                cell.fill = criterion_fill
                cell.alignment = wrap_alignment
                if col == 3:  # Points column
                    cell.alignment = center_alignment

            current_row += 1

        # Set column widths
        column_widths = {
            "A": 25,  # Criterion
            "B": 45,  # Description
            "C": 10,  # Points
            "D": 22,  # Threshold
            "E": 40,  # Notes
        }

        for col_letter, width in column_widths.items():
            worksheet.column_dimensions[col_letter].width = width

    def to_excel(self, filename: str) -> bytes:
        """Export the rubric to an Excel workbook and return its raw bytes."""
        excel_buffer = io.BytesIO()
        workbook = Workbook()

        self.to_excel_worksheet(workbook, filename)

        # Remove default sheet if it exists
        if "Sheet" in workbook.sheetnames:
            workbook.remove(workbook["Sheet"])

        workbook.save(excel_buffer)
        excel_buffer.seek(0)
        return excel_buffer.getvalue()
