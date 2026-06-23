import logging
from typing import ClassVar

from checks import (
    Check,
    CheckComplexity,
    CheckDetail,
    CheckDetailSection,
    CheckFormInput,
    CheckKeyValuePair,
    CheckKeyValueType,
    CheckResult,
    KeyValueFormInput,
)
from bpmn.bpmn import get_bpmn
from utils import get_elements_by_type
from utils.similarity import match_labels

logger = logging.getLogger(__name__)


def _pool_lane_detail(
    missing_pools: list[str],
    missing_lanes: list[str],
    extra_pools: list[str],
    extra_lanes: list[str],
) -> CheckDetail | None:
    """Build the info-pop-up breakdown, omitting empty sections.

    Missing pools/lanes (expected but absent) are errors; pools/lanes present in
    the submission with no expected counterpart are warnings.
    """
    sections: list[CheckDetailSection] = []
    if missing_pools:
        sections.append(CheckDetailSection(label="Missing pools", severity="error", items=missing_pools))
    if missing_lanes:
        sections.append(CheckDetailSection(label="Missing lanes", severity="error", items=missing_lanes))
    if extra_pools:
        sections.append(CheckDetailSection(label="Unmatched pools", severity="warn", items=extra_pools))
    if extra_lanes:
        sections.append(CheckDetailSection(label="Unmatched lanes", severity="warn", items=extra_lanes))
    return CheckDetail(sections=sections) if sections else None


class PoolLaneCheck(Check):
    id: ClassVar[str] = "pool_lane_check"
    name: ClassVar[str] = "Pool-Lane Check"
    description: ClassVar[str] = "Check for specific amount and label of the existing pools and lanes in a model"
    check_complexity: ClassVar[CheckComplexity] = CheckComplexity.CONFIGURABLE
    threshold: ClassVar[float] = 0.70

    key_label: ClassVar[str] = "Pool name"
    value_label: ClassVar[str] = "Lane name"
    input_scheme: ClassVar[list[CheckFormInput]] = [
        KeyValueFormInput(
            input_label="Pools and lanes",
            data=CheckKeyValueType(key_label=key_label, value_label=value_label, pairs=[]),
            multiple=True,
        ),
    ]

    def analyze(
        self,
        inputs: list[CheckFormInput] | None = None,
        threshold: float | None = None,
        ideal_threshold: float | None = None,
    ) -> CheckResult:
        if inputs is None:
            # Analyze pools & lanes whilst taking reference xml as ground truth.
            inputs = []
            model = get_bpmn(self.model_xml)

            if len(model.pools) == 0:
                raise Exception("No pools found")

            inputs.append(
                KeyValueFormInput(
                    input_label="Pool(s) and Lane(s)",
                    multiple=True,
                    data=CheckKeyValueType(
                        key_label=self.key_label,
                        value_label=self.value_label,
                        # In case a pool has a single lane, that lane has no name.
                        pairs=[
                            CheckKeyValuePair(
                                key=pool.name,
                                value=[lane.name for lane in pool.lanes if lane.name is not None],
                            )
                            for pool in model.pools
                        ],
                    ),
                )
            )

            return CheckResult(
                id=self.id,
                name=self.name,
                description=self.description,
                check_complexity=self.check_complexity,
                problematic_elements=[],
                fulfilled=True,
                inputs=inputs,
            )

        # Parse model_xml into Bpmn
        model = get_bpmn(self.model_xml)

        pools = [(pool.name, pool.participant_id or pool.id) for pool in model.pools]
        submission_pools = [pool[0] for pool in pools if pool[0] is not None]

        reference_pools: list[str] = []
        reference_pairs: list[CheckKeyValuePair] = []

        for v in inputs:
            if not isinstance(v, KeyValueFormInput):
                continue
            for pool in v.data.pairs:
                reference_pools.append(pool.key)
                reference_pairs.append(pool)

        if reference_pools and not submission_pools:
            return CheckResult(
                id=self.id,
                name=self.name,
                description=self.description,
                check_complexity=self.check_complexity,
                problematic_elements=[],
                fulfilled=None,
                inputs=inputs,
                detail=_pool_lane_detail(reference_pools, [], [], []),
            )

        pool_matches = match_labels(
            target=submission_pools,
            reference=reference_pools,
            match_threshold=self.threshold,
        )

        # Collect unmatched pool IDs as problematic, but continue to check lanes
        # for pools that did match.
        matched_pool_ids = {pools[submission_idx][1] for submission_idx, _ in pool_matches}
        missing_ids = [pool[1] for pool in pools if pool[0] is not None and pool[1] not in matched_pool_ids]
        has_count_mismatch = len(pool_matches) != len(reference_pools)

        # Human-readable breakdown for the criterion's (i) info pop-up, mirroring
        # Task Coverage: expected-but-absent = error, present-but-unexpected = warn.
        matched_ref_pool_idxs = {reference_idx for _, reference_idx in pool_matches}
        matched_sub_pool_idxs = {submission_idx for submission_idx, _ in pool_matches}
        missing_pools = [label for idx, label in enumerate(reference_pools) if idx not in matched_ref_pool_idxs]
        extra_pools = [label for idx, label in enumerate(submission_pools) if idx not in matched_sub_pool_idxs]
        missing_lanes: list[str] = []
        extra_lanes: list[str] = []

        for submission_idx, reference_idx in pool_matches:
            submission_lane_labels = [task.name for task in model.pools[submission_idx].lanes]

            reference_lane_labels: list[str] = reference_pairs[reference_idx].value
            pool_name = reference_pairs[reference_idx].key

            if not reference_lane_labels:
                # Pool with no expected lanes (e.g. closed/black-box pool) — nothing to check.
                continue

            if len(submission_lane_labels) != len(reference_lane_labels):
                has_count_mismatch = True

            lane_pairs = match_labels(
                target=submission_lane_labels,
                reference=reference_lane_labels,
                match_threshold=self.threshold,
            )

            matched_ref_lane_idxs = {ref_idx for _, ref_idx in lane_pairs}
            matched_sub_lane_idxs = {sub_idx for sub_idx, _ in lane_pairs}
            missing_lanes.extend(
                f"{pool_name}: {label}"
                for idx, label in enumerate(reference_lane_labels)
                if idx not in matched_ref_lane_idxs
            )
            extra_lanes.extend(
                f"{pool_name}: {label or '(unnamed lane)'}"
                for idx, label in enumerate(submission_lane_labels)
                if idx not in matched_sub_lane_idxs
            )

            if len(lane_pairs) != len(reference_lane_labels):
                current_lane = model.pools[submission_idx].lanes
                # Add unmatched pool ids to problematic elements list and return early
                matched_lane_ids = []
                for submission_lane_idx, _ in lane_pairs:
                    matched_lane_ids.append(current_lane[submission_lane_idx].id)

                missing_matches = set([lane.id for lane in current_lane if lane.id]).difference(matched_lane_ids)
                for missed_match in missing_matches:
                    missing_ids.append(missed_match)

        return CheckResult(
            id=self.id,
            name=self.name,
            description=self.description,
            check_complexity=self.check_complexity,
            problematic_elements=missing_ids,
            fulfilled=(len(missing_ids) == 0 and not has_count_mismatch),
            inputs=inputs,
            detail=_pool_lane_detail(missing_pools, missing_lanes, extra_pools, extra_lanes),
        )

    def is_applicable(self) -> bool:
        try:
            get_elements_by_type(self.model_xml, "process")
            get_elements_by_type(self.model_xml, "lane")
        except TypeError as e:
            logger.info("Check '%s' is not applicable: %s", self.name, e)
            return False
        except ValueError as e:
            logger.info("Check '%s' is not applicable: %s", self.name, e)
            return False

        return True
