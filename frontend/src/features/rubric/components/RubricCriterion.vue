<script lang="ts">
// Module-scoped (shared across every criterion instance): only one criterion
// popover may be open at a time. Opening one
// closes the previously open one. Needed because the trigger buttons use
// `@click.stop`, which suppresses PrimeVue's own outside-click dismissal.
type Dismissable = { hide: () => void };
let activePopover: Dismissable | null = null;

function trackPopoverOpen(popover: Dismissable): void {
  if (activePopover && activePopover !== popover) activePopover.hide();
  activePopover = popover;
}

function trackPopoverClose(popover: Dismissable): void {
  if (activePopover === popover) activePopover = null;
}
</script>

<script lang="ts" setup>
import {Check, Edit, ExternalLink, Info, Settings, Split, StickyNote, XIcon, Trash2} from "lucide-vue-next";
import {computed, nextTick, ref, useTemplateRef, watch} from "vue";
import Popover from "primevue/popover";
import {CheckComplexity} from "@/features/rubric/types/check_complexity.ts";
import type {Criterion} from "@/features/rubric/types/rubric";
import {isGroup as isGroupCriterion} from "@/features/behavior/types/group";

const emit = defineEmits(['toggle', 'reset', 'updatePoints', 'edit', 'delete', 'updateThreshold', 'updateNotes']);

const props = withDefaults(defineProps<{
  title?: string;
  description?: string;
  state?: boolean | null;
  points?: number;
  custom_score_set?: boolean;
  category?: CheckComplexity;
  criterion?: Criterion;
  isEditable?: boolean;
  // True only while grading a submission: enables the per-submission settings
  // gear (threshold override + grading note). Hidden when editing the rubric
  // definition (reference tab).
  gradingSubmission?: boolean;
}>(), {
  isEditable: true,
  gradingSubmission: false,
});

// Canonical "is this a group" predicate: the `group:` id prefix (see group.ts),
// not the condition field, so it agrees with RubricSidebar's routing.
const isGroup = computed(() => isGroupCriterion(props.criterion ?? {}));

const expanded = ref(false);

const toggleExpand = () => {
  expanded.value = !expanded.value;
};

// (i) info pop-up: shown only when the backend attached a detail breakdown with
// at least one non-empty section (e.g. Task Coverage's missing/extra tasks, or a
// duplicate check's matched pairs).
const detail = computed(() => props.criterion?.detail);
const hasDetail = computed(
    () => !!detail.value && detail.value.sections.some((s) => s.items.length > 0),
);

const detailPopover = ref();
const toggleDetail = (event: Event) => {
  detailPopover.value?.toggle(event);
};

// Coordinate the "one popover at a time" rule (see the module-scoped tracker
// above): every Popover reports its open/close here.
const onPopoverShow = (popover: { hide: () => void }) => trackPopoverOpen(popover);
const onPopoverHide = (popover: { hide: () => void }) => trackPopoverClose(popover);

const severityClass = (severity: 'error' | 'warn' | 'info'): string =>
    severity === 'error'
        ? 'text-red-600'
        : severity === 'warn'
            ? 'text-amber-600'
            : 'text-gray-600';

// (gear) per-submission threshold overrides. Shown only while grading a
// submission, for checks whose matching cut-offs are overridable. Some checks
// have only a minimum cut-off; those with an ideal one (the duplicate checks)
// expose a second field.
const supportsThreshold = computed(() => props.criterion?.supports_threshold === true);
const defaultThreshold = computed(() => props.criterion?.default_threshold ?? null);
const defaultIdealThreshold = computed(() => props.criterion?.default_ideal_threshold ?? null);
const hasIdeal = computed(() => defaultIdealThreshold.value !== null);
const thresholdOverride = computed(() => props.criterion?.threshold_override ?? null);
const idealThresholdOverride = computed(() => props.criterion?.ideal_threshold_override ?? null);
// Per-check labels/help so the gear reads correctly (a "minimum" can mean
// opposite leniency directions across checks). Fall back to generic wording.
const thresholdLabel = computed(() => props.criterion?.threshold_label ?? 'Minimum');
const idealThresholdLabel = computed(() => props.criterion?.ideal_threshold_label ?? 'Ideal');
const thresholdHint = computed(() => props.criterion?.threshold_hint ?? null);
// Deviation badge on the gear: a non-default cut-off for this submission.
const hasThresholdOverride = computed(
    () => thresholdOverride.value !== null || idealThresholdOverride.value !== null,
);
const hasNotes = computed(() => !!props.criterion?.notes);

const settingsPopover = ref();
const minDraft = ref<number | null>(null);
const idealDraft = ref<number | null>(null);

const toggleSettings = (event: Event) => {
  // Seed drafts from the current criterion each time the pop-up opens.
  minDraft.value = thresholdOverride.value ?? defaultThreshold.value;
  idealDraft.value = idealThresholdOverride.value ?? defaultIdealThreshold.value;
  notesDraft.value = props.criterion?.notes ?? '';
  settingsPopover.value?.toggle(event);
};

function _valid(n: unknown): n is number {
  return typeof n === 'number' && !Number.isNaN(n) && n > 0 && n <= 1;
}

// The ideal cut-off must sit above the minimum (a "confident" match is stricter
// than a "candidate" one). Surfaced as an inline error and gates Apply.
const idealBelowMin = computed(
    () => hasIdeal.value && _valid(idealDraft.value) && _valid(minDraft.value)
        && idealDraft.value <= minDraft.value,
);
const minValid = computed(() => _valid(minDraft.value));
const idealValid = computed(
    () => !hasIdeal.value
        || (_valid(idealDraft.value) && _valid(minDraft.value) && idealDraft.value > minDraft.value),
);
// Threshold inputs are only gated for checks that actually expose them; for a
// note-only criterion there is nothing to validate.
const thresholdInputsValid = computed(
    () => !supportsThreshold.value || (minValid.value && idealValid.value),
);
// Whether the threshold drafts differ from the values the criterion was last
// graded with — i.e. an Apply would trigger a re-grade.
const thresholdChanged = computed(() => {
  if (!supportsThreshold.value) return false;
  if (minDraft.value !== (thresholdOverride.value ?? defaultThreshold.value)) return true;
  return hasIdeal.value
      && idealDraft.value !== (idealThresholdOverride.value ?? defaultIdealThreshold.value);
});

// Grading note draft. Seeded when the pop-up opens (toggleSettings) and re-synced
// when the criterion changes (e.g. switching submissions).
const notesDraft = ref<string>(props.criterion?.notes ?? '');
watch(() => props.criterion?.notes, (n) => (notesDraft.value = n ?? ''));
const notesChanged = computed(
    () => notesDraft.value.trim() !== (props.criterion?.notes ?? ''),
);

const canApply = computed(
    () => thresholdInputsValid.value && (thresholdChanged.value || notesChanged.value),
);

// Apply persists the note (no re-grade) and, only when a cut-off actually changed,
// re-grades the criterion server-side. The backend records a threshold override
// only when a value differs from the check's default, so leaving a field at its
// default is a no-op deviation.
function applySettings() {
  if (!canApply.value) return;
  if (thresholdChanged.value && _valid(minDraft.value)) {
    const ideal = hasIdeal.value && _valid(idealDraft.value) ? idealDraft.value : null;
    emit('updateThreshold', minDraft.value, ideal);
  }
  if (notesChanged.value) {
    const next = notesDraft.value.trim();
    emit('updateNotes', next === '' ? null : next);
  }
  settingsPopover.value?.hide();
}

function resetThresholds() {
  minDraft.value = defaultThreshold.value;
  idealDraft.value = defaultIdealThreshold.value;
  emit('updateThreshold', null, null);
  settingsPopover.value?.hide();
}


const editing = ref(false);
const draft = ref(props.points);
// Template ref (instance-scoped) — a document-global id="points-input" would
// collide across the many criterion cards rendered at once.
const pointsInput = useTemplateRef<HTMLInputElement>('pointsInput');

function startEdit() {
  editing.value = true;
  draft.value = props.points;
  void nextTick(() => pointsInput.value?.select());
}

function finishEdit() {
  editing.value = false;
  emit('updatePoints', draft.value);
}


</script>

<template>
  <div class="flex flex-col bg-white border min-h-28 h-auto w-full px-2 rounded-md shadow-sm transition-all duration-200">
    <div class="flex flex-row min-h-28 w-full">
    <div class="flex flex-col justify-start items-center py-2">
      <!-- Status box (varies by state) -->
      <div v-if="state === null" class="bg-yellow-600 cursor-pointer flex justify-center items-center h-16 w-16 rounded-t-sm">
        <span class="text-3xl text-white">?</span>
      </div>
      <button v-else-if="state && custom_score_set" type="button" aria-label="Reset to default score"
           class="bg-orange-400 text-white cursor-pointer flex justify-center items-center h-16 w-16 rounded-t-sm focus:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-white"
           @click.stop="$emit('reset')">
        <Split :size="36"/>
      </button>
      <button v-else-if="state" type="button" aria-label="Mark as not fulfilled"
           class="bg-green-600 text-white cursor-pointer flex justify-center items-center h-16 w-16 rounded-t-sm focus:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-white"
           @click.stop="$emit('toggle')">
        <Check :size="36"/>
      </button>
      <button v-else type="button" aria-label="Mark as fulfilled"
           class="bg-red-600 text-white cursor-pointer flex justify-center items-center h-16 w-16 rounded-t-sm focus:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-white"
           @click.stop="$emit('toggle')">
        <XIcon :size="36"/>
      </button>

      <!-- Points: read-only when ungraded (state === null), editable otherwise -->
      <p v-if="state === null"
         class="bg-gray-50 text-gray-700 border border-gray-200 w-full h-8 flex justify-center items-center font-semibold rounded-b-sm">
        {{ props.points }}</p>
      <input
          v-else-if="editing"
          ref="pointsInput"
          v-model.number="draft"
          class="bg-gray-50 text-gray-700 border border-gray-200 w-16 h-8 flex justify-center items-center font-semibold rounded-b-sm text-center outline-none"
          step="0.1"
          type="number"
          @blur="finishEdit"
          @keyup.enter="finishEdit"
      />
      <p
          v-else
          class="bg-gray-50 text-gray-700 border border-gray-200 w-full h-8 flex justify-center items-center font-semibold rounded-b-sm cursor-pointer select-none"
          @dblclick="startEdit"
      >
        {{ props.points }}
      </p>
    </div>
    <div class="my-2 bg-gray-50 border border-gray-200 rounded-sm flex-1 min-w-0 ml-2 p-2 flex flex-col relative">
      <div class="flex items-center gap-2 pb-2">
        <span class="font-semibold uppercase text-md text-gray-800">{{ title }}</span>
        <span v-if="props.criterion?.condition === 'XOR'" class="bg-blue-500 text-white text-xs font-bold px-1.5 py-0.5 rounded">XOR</span>
        <span v-if="props.criterion?.condition === 'AND'" class="bg-green-500 text-white text-xs font-bold px-1.5 py-0.5 rounded">AND</span>
      </div>
      <div class="flex flex-col flex-1 mr-8">
        <p class="text-gray-600 text-sm flex-1">{{ description }}</p>
      </div>
      <div v-if="gradingSubmission && !isGroup && criterion?.notes"
           class="mt-2 flex items-start gap-1.5 bg-amber-50 border border-amber-200 rounded-sm px-2 py-1">
        <StickyNote :size="14" class="mt-0.5 shrink-0 text-amber-500"/>
        <p class="min-w-0 flex-1 text-sm text-gray-700 whitespace-pre-wrap wrap-break-word">{{ criterion.notes }}</p>
      </div>
      <div class="flex items-center pr-2 absolute right-0">
        <button v-if="hasDetail" class="p-2 hover:bg-gray-100 rounded-md transition-colors"
                title="Details"
                @click.stop="toggleDetail">
          <Info :size="20" class="text-gray-500"/>
        </button>
        <button v-if="gradingSubmission && !isGroup"
                class="relative p-2 hover:bg-gray-100 rounded-md transition-colors"
                :title="supportsThreshold ? 'Settings' : 'Grading note'"
                @click.stop="toggleSettings">
          <Settings v-if="supportsThreshold" :size="20" :class="hasThresholdOverride ? 'text-blue-500' : 'text-gray-500'"/>
          <StickyNote v-else :size="20" :class="hasNotes ? 'text-blue-500' : 'text-gray-500'"/>
          <span v-if="supportsThreshold ? hasThresholdOverride : hasNotes" class="absolute top-1 right-1 h-2 w-2 rounded-full bg-blue-500"/>
        </button>
        <button v-if="category === CheckComplexity.COMPLEX || (category !== CheckComplexity.SIMPLE && isEditable)" class="p-2 hover:bg-gray-100 rounded-md transition-colors" :title="isEditable ? 'Edit rule' : 'View rule'"
                @click.stop="$emit('edit')">

          <Edit v-if="category !== CheckComplexity.COMPLEX" :size="20" class="text-gray-600"/>
          <ExternalLink v-else :size="20" class="text-gray-600"/>
        </button>
        <button v-if="isEditable" class="p-2 hover:bg-gray-100 rounded-md transition-colors" title="Delete criterion"
                @click.stop="$emit('delete')">
          <Trash2 :size="20" class="text-red-500"/>
        </button>
      </div>
      
      <div v-if="isGroup" class="mt-2 text-xs">
        <button
          class="text-blue-600 hover:underline focus:outline-none flex items-center gap-1"
          @click.stop="toggleExpand"
        >
          {{ expanded ? 'Hide details' : 'Show details' }}
          <span v-if="criterion?.rule_results">({{ criterion.rule_results.length }} rules)</span>
        </button>
      </div>

      <Popover ref="detailPopover" @show="onPopoverShow(detailPopover)" @hide="onPopoverHide(detailPopover)">
        <div class="max-w-xs text-sm">
          <div
            v-for="(section, si) in detail?.sections ?? []"
            v-show="section.items.length"
            :key="si"
            class="mb-3 last:mb-0"
          >
            <p class="font-semibold mb-1" :class="severityClass(section.severity)">
              {{ section.label }} ({{ section.items.length }})
            </p>
            <ul class="list-disc list-inside text-gray-700 space-y-0.5">
              <li v-for="(item, ii) in section.items" :key="ii">{{ item }}</li>
            </ul>
          </div>
        </div>
      </Popover>

      <Popover ref="settingsPopover" @show="onPopoverShow(settingsPopover)" @hide="onPopoverHide(settingsPopover)">
        <div class="w-96 text-sm text-gray-700">
          <template v-if="supportsThreshold">
            <p class="font-semibold text-gray-800 mb-1">Matching thresholds</p>
            <p class="text-xs text-gray-500 mb-3">
              {{ thresholdHint ?? 'Adjust how strict the match must be for this submission only, then apply to re-grade.' }}
            </p>

            <div class="flex items-center justify-between gap-2 mb-2">
              <label class="text-gray-700">
                {{ thresholdLabel }}
                <span class="text-xs text-gray-400">(default {{ defaultThreshold }})</span>
              </label>
              <input
                  v-model.number="minDraft"
                  class="border border-gray-300 rounded-md w-20 px-2 py-1 outline-none focus:border-blue-500"
                  max="1"
                  min="0"
                  step="0.05"
                  type="number"
                  @keyup.enter="applySettings"
              />
            </div>

            <div v-if="hasIdeal" class="flex items-center justify-between gap-2 mb-1">
              <label class="text-gray-700">
                {{ idealThresholdLabel }}
                <span class="text-xs text-gray-400">(default {{ defaultIdealThreshold }})</span>
              </label>
              <input
                  v-model.number="idealDraft"
                  :class="idealBelowMin ? 'border-red-400' : 'border-gray-300'"
                  class="border rounded-md w-20 px-2 py-1 outline-none focus:border-blue-500"
                  max="1"
                  min="0"
                  step="0.05"
                  type="number"
                  @keyup.enter="applySettings"
              />
            </div>
            <p v-if="idealBelowMin" class="text-xs text-red-500 mb-1">
              The upper value must be greater than the lower one.
            </p>
          </template>

          <div :class="supportsThreshold ? 'mt-4 pt-3 border-t border-gray-200' : ''">
            <p class="font-semibold text-gray-800 mb-1">Grading note</p>
            <p class="text-xs text-gray-500 mb-2">
              Saved with the submission. Does not re-grade.
            </p>
            <textarea
                v-model="notesDraft"
                class="w-full text-sm text-gray-700 bg-white border border-gray-300 rounded-md px-2 py-1 outline-none focus:border-blue-500 resize-y min-h-16"
                placeholder="Add a grading note…"
                rows="3"
                @click.stop
            />
          </div>

          <div class="flex items-center justify-end gap-3 mt-3">
            <button
                v-if="hasThresholdOverride"
                class="text-xs text-gray-500 hover:underline"
                @click.stop="resetThresholds"
            >
              Reset thresholds
            </button>
            <button
                :disabled="!canApply"
                class="text-xs font-semibold text-white bg-blue-600 hover:bg-blue-700 rounded-md px-3 py-1.5 transition-colors disabled:bg-gray-300 disabled:cursor-not-allowed"
                @click.stop="applySettings"
            >
              Apply
            </button>
          </div>
        </div>
      </Popover>
    </div>
  </div>

  <div v-if="expanded && isGroup && criterion?.rule_results" class="px-4 pb-4 w-full">
    <div class="bg-gray-50 border border-gray-200 rounded-sm p-2 text-sm space-y-2">
      <div 
        v-for="rule in criterion.rule_results" 
        :key="rule.rule_id"
        class="flex justify-between items-center p-2 rounded"
        :class="{'bg-yellow-50 border border-yellow-200': rule.rule_id === criterion.best_rule_id && criterion.condition === 'XOR'}"
      >
        <div class="flex flex-col">
          <span class="font-medium" :class="{'text-yellow-700': rule.rule_id === criterion.best_rule_id && criterion.condition === 'XOR'}">
            {{ rule.rule_name }}
            <span v-if="rule.rule_id === criterion.best_rule_id && criterion.condition === 'XOR'" class="ml-2 text-xs text-yellow-600 font-bold">★ Best Match</span>
          </span>
          <span class="text-xs text-gray-500">Confidence: {{ (rule.confidence * 100).toFixed(0) }}%</span>
        </div>
        <div class="flex items-center gap-2">
          <span :class="rule.success ? 'text-green-600' : 'text-red-600'" class="font-bold">
            {{ rule.earned_points?.toFixed(2) }}
          </span>
          <Check v-if="rule.success" :size="16" class="text-green-600"/>
          <XIcon v-else :size="16" class="text-red-600"/>
        </div>
      </div>
    </div>
  </div>
  </div>
</template>