<script lang="ts" setup>
import { computed, onMounted, ref, watch } from 'vue';
import { StickyNote, Trash2 } from 'lucide-vue-next';
import Popover from 'primevue/popover';
import { Criterion } from "@/features/rubric/types/rubric";
import RubricCriterion from "@/features/rubric/components/RubricCriterion.vue";
import { CheckComplexity } from "@/features/rubric/types/check_complexity";
import { groupService } from "@/services/groupService";
import { getGroupId } from "@/features/behavior/types/group";
import { BehavioralRuleGroup } from "@/features/behavior/types/group";

const props = withDefaults(defineProps<{
  criterion: Criterion;
  isEditable?: boolean;
  submissionFilename?: string;
}>(), {
  isEditable: true
});

const emit = defineEmits<{
  'toggleHighlight': [index: number, problematicElements: string[]];
  'editCriterion': [criterion: Criterion];
  'updateNotes': [internalNotes: string | null, feedbackNotes: string | null];
  'delete': [];
}>();

// The group *definition* (condition, maxPoints, name) is static and fetched
// once. All scores come from the composed criterion's per-model `group_result`,
// so they're always correct for the model currently being viewed (no staleness).
const groupDef = ref<BehavioralRuleGroup | null>(null);

const loadGroupDef = async () => {
  try {
    groupDef.value = await groupService.getGroup(getGroupId(props.criterion));
  } catch (e) {
    console.error("Failed to fetch group definition", e);
  }
};

onMounted(loadGroupDef);
watch(() => props.criterion.id, loadGroupDef);

const ruleResults = computed(() => props.criterion.group_result?.rule_results ?? []);
const bestRuleId = computed(() => props.criterion.group_result?.best_rule_id ?? null);

// Map per-rule results to Criterion-like objects for the inner RubricCriterion
const innerCriteria = computed(() =>
  ruleResults.value.map(result => ({
    title: result.rule_name,
    description: result.description,
    state: result.success && result.earned_points > 0,
    points: result.earned_points,
    custom_score_set: false,
    category: CheckComplexity.COMPLEX,
    id: result.rule_id,
    name: result.rule_name,
    // Prefer the persisted per-rule list; fall back to mining match_details
    // (present only on the live validate/analyze response).
    problematic_elements:
      result.problematic_elements ?? result.match_details?.map(m => m.bpmn_element_id) ?? []
  }))
);

const condition = computed(() => props.criterion.condition ?? groupDef.value?.condition);
const isXor = computed(() => condition.value === 'XOR');
const isAnd = computed(() => condition.value === 'AND');

const maxScore = computed(() =>
  groupDef.value?.maxPoints ?? props.criterion.maxPoints ?? props.criterion.default_points ?? 0
);

const currentScore = computed(() => {
  if (props.criterion.group_result) return props.criterion.group_result.earned_points;
  if (props.criterion.score !== null && props.criterion.score !== undefined) {
    return props.criterion.score;
  }
  return 0;
});

const bestRuleName = computed(() => {
  if (!bestRuleId.value) return undefined;
  const bestRule = ruleResults.value.find(r => r.rule_id === bestRuleId.value);
  return bestRule ? `Max points derived from rule: ${bestRule.rule_name}` : undefined;
});

// Editing an inner rule opens its behavior editor; handleEditCriterion only
// reads id + check_complexity, but we return a full Criterion so the emit is
// typed rather than `any`.
const toEditCriterion = (item: (typeof innerCriteria.value)[number]): Criterion => ({
  id: item.id,
  name: item.name,
  description: item.description ?? '',
  check_complexity: CheckComplexity.COMPLEX,
  fulfilled: item.state,
  default_points: item.points,
  score: null,
  problematic_elements: item.problematic_elements,
});

// Group-level grading notes (internal = between graders, feedback = for the
// student). A group's rules combine into one judged unit, so the note lives on
// the group itself rather than per rule. Submission-scoped: only editable while
// grading a submission.
const gradingSubmission = computed(() => !!props.submissionFilename);
const hasNotes = computed(
  () => !!props.criterion.internal_notes || !!props.criterion.feedback_notes,
);

const notesPopover = ref();
const internalDraft = ref<string>(props.criterion.internal_notes ?? '');
const feedbackDraft = ref<string>(props.criterion.feedback_notes ?? '');
watch(() => props.criterion.internal_notes, (n) => (internalDraft.value = n ?? ''));
watch(() => props.criterion.feedback_notes, (n) => (feedbackDraft.value = n ?? ''));

const notesChanged = computed(
  () => internalDraft.value.trim() !== (props.criterion.internal_notes ?? '')
    || feedbackDraft.value.trim() !== (props.criterion.feedback_notes ?? ''),
);

const toggleNotes = (event: Event) => {
  // Seed drafts from the criterion each time the pop-up opens.
  internalDraft.value = props.criterion.internal_notes ?? '';
  feedbackDraft.value = props.criterion.feedback_notes ?? '';
  notesPopover.value?.toggle(event);
};

const applyNotes = () => {
  if (!notesChanged.value) return;
  const internal = internalDraft.value.trim();
  const feedback = feedbackDraft.value.trim();
  emit('updateNotes', internal === '' ? null : internal, feedback === '' ? null : feedback);
  notesPopover.value?.hide();
};
</script>

<template>
  <div class="bg-white border rounded-lg shadow-sm mb-4 overflow-hidden">
    <!-- Group Header -->
    <div class="bg-gray-50 border-b px-4 py-3 flex justify-between items-center">
      <div class="flex flex-col">
        <div class="flex items-center gap-2">
          <span class="font-bold text-gray-800">{{ criterion.name }}</span>
          <span v-if="isXor" class="bg-blue-500 text-white text-xs font-bold px-1.5 py-0.5 rounded">XOR</span>
          <span v-if="isAnd" class="bg-green-500 text-white text-xs font-bold px-1.5 py-0.5 rounded">AND</span>
        </div>
      </div>
      <div class="flex items-center gap-2">
        <button v-if="gradingSubmission"
                class="relative p-1 hover:bg-gray-100 rounded-md transition-colors"
                title="Grading notes"
                @click.stop="toggleNotes">
          <StickyNote :size="18" :class="hasNotes ? 'text-blue-500' : 'text-gray-500'"/>
          <span v-if="hasNotes" class="absolute top-0 right-0 h-2 w-2 rounded-full bg-blue-500"/>
        </button>
        <div class="flex flex-col items-end">
          <span
              class="text-sm font-semibold cursor-help"
              :class="criterion.fulfilled ? 'text-green-600' : 'text-gray-600'"
              :title="bestRuleName"
          >
            {{ currentScore.toFixed(2) }} / {{ maxScore.toFixed(2) }}
          </span>
          <span class="text-xs text-gray-400">Group Score</span>
          <button v-if="isEditable" class="p-1 hover:bg-gray-100 rounded-md transition-colors mt-1" title="Delete group"
                  @click.stop="$emit('delete')">
            <Trash2 :size="16" class="text-red-500"/>
          </button>
        </div>
      </div>
    </div>

    <!-- Group grading notes (shown while grading a submission) -->
    <div v-if="gradingSubmission && criterion.internal_notes"
         class="mx-2 mt-2 flex items-start gap-1.5 bg-amber-50 border border-amber-200 rounded-sm px-2 py-1">
      <StickyNote :size="14" class="mt-0.5 shrink-0 text-amber-500"/>
      <div class="min-w-0 flex-1">
        <p class="text-xs font-semibold text-amber-700">Internal note</p>
        <p class="text-sm text-gray-700 whitespace-pre-wrap wrap-break-word">{{ criterion.internal_notes }}</p>
      </div>
    </div>
    <div v-if="gradingSubmission && criterion.feedback_notes"
         class="mx-2 mt-2 flex items-start gap-1.5 bg-sky-50 border border-sky-200 rounded-sm px-2 py-1">
      <StickyNote :size="14" class="mt-0.5 shrink-0 text-sky-500"/>
      <div class="min-w-0 flex-1">
        <p class="text-xs font-semibold text-sky-700">Feedback for student</p>
        <p class="text-sm text-gray-700 whitespace-pre-wrap wrap-break-word">{{ criterion.feedback_notes }}</p>
      </div>
    </div>

    <Popover ref="notesPopover">
      <div class="w-96 text-sm text-gray-700">
        <p class="font-semibold text-gray-800 mb-1">Internal note</p>
        <p class="text-xs text-gray-500 mb-2">
          Only seen by graders. Saved with the submission; does not re-grade.
        </p>
        <textarea
            v-model="internalDraft"
            class="w-full text-sm text-gray-700 bg-white border border-gray-300 rounded-md px-2 py-1 outline-none focus:border-blue-500 resize-y min-h-16"
            placeholder="Add an internal note…"
            rows="3"
            @click.stop
        />
        <p class="font-semibold text-gray-800 mb-1 mt-3">Feedback for student</p>
        <p class="text-xs text-gray-500 mb-2">
          Intended for the student. Saved with the submission; does not re-grade.
        </p>
        <textarea
            v-model="feedbackDraft"
            class="w-full text-sm text-gray-700 bg-white border border-gray-300 rounded-md px-2 py-1 outline-none focus:border-blue-500 resize-y min-h-16"
            placeholder="Add feedback for the student…"
            rows="3"
            @click.stop
        />
        <div class="flex items-center justify-end mt-3">
          <button
              :disabled="!notesChanged"
              class="text-xs font-semibold text-white bg-blue-600 hover:bg-blue-700 rounded-md px-3 py-1.5 transition-colors disabled:bg-gray-300 disabled:cursor-not-allowed"
              @click.stop="applyNotes"
          >
            Apply
          </button>
        </div>
      </div>
    </Popover>

    <!-- Inner Criteria List -->
    <div class="p-2 flex flex-col gap-2 bg-gray-50/50">
      <RubricCriterion
        v-for="item in innerCriteria"
        :key="item.id"
        :title="item.title"
        :description="item.description"
        :state="item.state"
        :points="item.points"
        :custom_score_set="false"
        :category="item.category"
        class="border-gray-200"
        :class="{'border-l-4 border-l-yellow-400': isXor && item.id === bestRuleId}"
        :is-editable="isEditable"
        @edit="emit('editCriterion', toEditCriterion(item))"
        @click="emit('toggleHighlight', -1, item.problematic_elements)"
      />
      <!-- Note: ToggleHighlight index -1 is a placeholder... -->
    </div>
  </div>
</template>
