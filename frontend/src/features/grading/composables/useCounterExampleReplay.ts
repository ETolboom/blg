import type BpmnModeler from "bpmn-js/lib/Modeler";
// @ts-expect-error - plain-JS vendored module, no type declarations
import {
    START_COUNTER_EXAMPLE_VISUALIZATION,
    TOGGLE_MODE_EVENT,
} from "@/features/bpmn/extensions/counter-example-visualization/util/EventHelper";
import type {
    Criterion,
    CounterExample,
    CounterExampleState,
} from "@/features/rubric/types/rubric";

// The visualization modules (ported from bpmn-analyzer-js) read token and message
// counts as JS `Map`s, but the backend delivers them as plain JSON objects. Convert
// before firing the start event so the replay can step through the trace.
function toState(state: CounterExampleState) {
    return {
        snapshots: (state.snapshots ?? []).map((s) => ({
            id: s.id,
            tokens: new Map(Object.entries(s.tokens ?? {})),
        })),
        messages: new Map(Object.entries(state.messages ?? {})),
        executed_end_event_counter: new Map(
            Object.entries(state.executed_end_event_counter ?? {}),
        ),
    };
}

function toCounterExample(ce: CounterExample) {
    return {
        start_state: toState(ce.start_state),
        transitions: (ce.transitions ?? []).map((t) => ({
            label: t.label,
            next_state: toState(t.next_state),
        })),
    };
}

/**
 * Drives the on-diagram token replay for a control-flow criterion's counterexample.
 *
 * `start` fires the visualization start event on the modeler's event bus (which
 * shows the play/pause/restart/speed/log controls and animates tokens along the
 * path to the violating state). `stop` fires the toggle-off event, which the
 * animation/token/message modules listen to in order to clear the diagram.
 */
export function useCounterExampleReplay() {
    function start(modeler: BpmnModeler, criterion: Criterion): boolean {
        if (!criterion.counter_example) return false;

        const eventBus = modeler.get("eventBus");
        eventBus.fire(START_COUNTER_EXAMPLE_VISUALIZATION, {
            propertyResult: {
                property: criterion.name,
                fulfilled: false,
                problematic_elements: criterion.problematic_elements ?? [],
                counter_example: toCounterExample(criterion.counter_example),
            },
        });
        return true;
    }

    function stop(modeler: BpmnModeler): void {
        modeler.get("eventBus").fire(TOGGLE_MODE_EVENT, { active: false });
    }

    return { start, stop };
}
