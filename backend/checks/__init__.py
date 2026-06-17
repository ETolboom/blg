from abc import ABC, abstractmethod
from enum import Enum
from typing import Annotated, ClassVar, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)


class CheckInputType(str, Enum):
    STRING = "string"
    INTEGER = "integer"
    KEY_VALUE = "key-value"
    SELECTION = "selection"


class CheckKeyValuePair(BaseModel):
    key: str
    value: list[str]


class CheckSelectionPair(BaseModel):
    label: str
    type: str


class CheckSelectionType(BaseModel):
    placeholder: str
    accepted_values: list[str]
    pairs: list[CheckSelectionPair]


class CheckKeyValueType(BaseModel):
    pairs: list[CheckKeyValuePair] = []
    key_label: str = Field(description="Label for outer key e.g. Pool-Name")
    value_label: str = Field(description="Label for inner list items e.g. Lane-Name")


class _FormInputBase(BaseModel):
    """Shared fields for a check's configurable form input.

    Concrete inputs are discriminated on ``input_type`` (see ``CheckFormInput``),
    so each variant carries a correctly-typed ``data`` field. This is what keeps
    the wire contract type-safe end to end: Pydantic rejects a payload whose
    ``data`` shape doesn't match its declared ``input_type``, and the frontend
    mirror (services/checkService.ts) narrows on the same discriminator.
    """

    # Label for the input
    input_label: str

    # Allow multiple inputs of this type (single string/int -> a list)
    multiple: bool = False


class StringFormInput(_FormInputBase):
    input_type: Literal[CheckInputType.STRING] = CheckInputType.STRING
    data: str | list[str]


class IntegerFormInput(_FormInputBase):
    input_type: Literal[CheckInputType.INTEGER] = CheckInputType.INTEGER
    data: int | list[int]


class KeyValueFormInput(_FormInputBase):
    input_type: Literal[CheckInputType.KEY_VALUE] = CheckInputType.KEY_VALUE
    data: CheckKeyValueType


class SelectionFormInput(_FormInputBase):
    input_type: Literal[CheckInputType.SELECTION] = CheckInputType.SELECTION
    data: CheckSelectionType


CheckFormInput = Annotated[
    StringFormInput | IntegerFormInput | KeyValueFormInput | SelectionFormInput,
    Field(discriminator="input_type"),
]


class CheckComplexity(str, Enum):
    SIMPLE = "0"
    CONFIGURABLE = "1"
    COMPLEX = "2"


class CheckDetailSection(BaseModel):
    """One labeled group of human-readable lines for a criterion's (i) info
    pop-up. ``severity`` drives the colour the frontend renders it in."""

    label: str
    severity: Literal["error", "warn", "info"] = "info"
    items: list[str] = []


class CheckDetail(BaseModel):
    """Optional breakdown shown in a criterion's info pop-up. Generic across
    checks: Task Coverage lists missing/extra tasks; the duplicate checks list
    the matched pairs."""

    sections: list[CheckDetailSection] = []


class CounterExampleSnapshot(BaseModel):
    """Token marking of one process (or sub-process) instance in a state:
    ``tokens`` maps a flow-element id to the number of tokens sitting on it."""

    id: str
    tokens: dict[str, int] = {}


class CounterExampleState(BaseModel):
    """A single reachable state in a counterexample trace."""

    snapshots: list[CounterExampleSnapshot] = []
    messages: dict[str, int] = {}
    executed_end_event_counter: dict[str, int] = {}


class CounterExampleTransition(BaseModel):
    """One step of the trace: firing the flow node ``label`` yields ``next_state``."""

    label: str
    next_state: CounterExampleState


class CounterExample(BaseModel):
    """The path from the start state to the first problematic state, used by the
    front-end to animate a token replay showing *how* a control-flow violation
    (e.g. a deadlock) is reached. Produced by the Rust analyzer bindings."""

    start_state: CounterExampleState
    transitions: list[CounterExampleTransition] = []


class CheckResult(BaseModel):
    """This class describes the format in which the algorithm is presented."""

    id: str
    name: str
    check_complexity: CheckComplexity
    description: str = ""
    # None = indeterminate ("?"): the check ran but the outcome needs a human look
    # (e.g. Task Coverage when all expected tasks are present but extras exist).
    fulfilled: bool | None
    confidence: float = 1.0
    problematic_elements: list[str] = []
    inputs: list[CheckFormInput] = []
    detail: CheckDetail | None = None
    # Token-replay trace for control-flow violations; None when not applicable.
    counter_example: CounterExample | None = None


class ThresholdMeta(BaseModel):
    supports: bool = False
    default_threshold: float | None = None
    default_ideal_threshold: float | None = None
    threshold_label: str | None = None
    ideal_threshold_label: str | None = None
    threshold_hint: str | None = None


class Check(BaseModel, ABC):
    """Every check must implement this class."""

    model_config = ConfigDict(extra="ignore", strict=True)

    # These fields must be defined as class attributes with defaults in subclasses
    id: ClassVar[str]
    name: ClassVar[str]
    description: ClassVar[str]
    check_complexity: ClassVar[CheckComplexity]
    threshold: ClassVar[float] = 0.0
    ideal_threshold: ClassVar[float | None] = None
    supports_threshold_override: ClassVar[bool] = False
    threshold_label: ClassVar[str] = "Minimum"
    ideal_threshold_label: ClassVar[str | None] = None
    threshold_hint: ClassVar[str | None] = None
    input_scheme: ClassVar[list[CheckFormInput]]
    awards_points: ClassVar[bool] = True

    # This field must be provided at instantiation
    model_xml: str

    @classmethod
    def load_dependencies(cls) -> None:
        """
        Load any heavy dependencies (ML models, etc.) required by this check.

        This method is called once during startup before any checks are instantiated.
        Subclasses should override this to load models, tokenizers, etc.

        Example:
            @classmethod
            def load_dependencies(cls) -> None:
                global _my_model
                if _my_model is None:
                    print(f"Loading model for {cls.name}...")
                    _my_model = load_expensive_model()
        """
        pass  # Default: no dependencies

    @abstractmethod
    def analyze(
        self,
        inputs: list[CheckFormInput] | None,
        threshold: float | None = None,
        ideal_threshold: float | None = None,
    ) -> CheckResult:
        """Analyze a given property based on inputs if available.

        ``threshold`` / ``ideal_threshold`` are optional per-submission overrides
        for the check's matching cut-offs; ``None`` means "use the class default"
        (``threshold`` / ``ideal_threshold``). Only meaningful for checks with
        ``supports_threshold_override = True`` (and ``ideal_threshold`` only for
        those that define one).
        """
        pass

    @abstractmethod
    def is_applicable(self) -> bool:
        """Check to see whether a check is applicable to a given model"""
        pass
