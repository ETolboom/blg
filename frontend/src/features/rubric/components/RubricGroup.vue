<script lang="ts" setup>
import { computed, onMounted, ref, watch } from 'vue';
import { Trash2 } from 'lucide-vue-next';
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
  'editCriterion': [criterion: any];
  'delete': [];
}>();

const groupDetails = ref<BehavioralRuleGroup | null>(null);

const loadGroupDetails = async () => {
    try {
        const id = getGroupId(props.criterion);
        const group = await groupService.getGroup(id, props.submissionFilename);
        groupDetails.value = group;
        // No need to fetch individual templates anymore, backend provides them.
    } catch (e) {
        console.error("Failed to fetch group details", e);
    }
};

const refreshGroupDetails = async () => {
  const criterion = props.criterion as any;
  // Only use embedded evaluation results if we're viewing a specific submission.
  // When viewing the reference (no submissionFilename), the embedded earned_points
  // belong to the last-graded submission and would show stale/wrong scores.
  if (props.submissionFilename && criterion.earned_points !== undefined && criterion.earned_points !== null) {
    // Criterion already has embedded evaluation results — use them directly.
    groupDetails.value = criterion as BehavioralRuleGroup;
  } else {
    // No embedded results, or we're on the reference view: hit the API.
    await loadGroupDetails();
  }
};

onMounted(refreshGroupDetails);

// Re-evaluate whenever the criterion data or the active submission changes.
// onMounted only runs once, so switching submissions wouldn't update groupDetails otherwise.
watch(
  [() => props.criterion, () => props.submissionFilename],
  refreshGroupDetails,
  { deep: true }
);

// Map rule results to Criterion-like objects for the inner RubricCriterion
const innerCriteria = computed(() => {
  if (groupDetails.value?.rule_results) {
    return groupDetails.value.rule_results.map(result => {
        // Use description from result if available, OR look it up in enriched rules
        return {
            title: result.rule_name,
            description: result.description,
            state: result.success && result.earned_points > 0,
            points: result.earned_points,
            custom_score_set: false,
            category: CheckComplexity.COMPLEX,
            id: result.rule_id,
            name: result.rule_name,
            problematic_elements: result.match_details?.map(m => m.bpmn_element_id) || []
        };
    });
  }

  return [];
});

const isXor = computed(() => (props.criterion.condition || groupDetails.value?.condition) === 'XOR');
const isAnd = computed(() => (props.criterion.condition || groupDetails.value?.condition) === 'AND');
const maxScore = computed(() => {
  return groupDetails.value?.maxPoints ?? props.criterion.maxPoints ?? props.criterion.default_points ?? 0;
});

const currentScore = computed(() => {
  // Prioritize freshly-fetched group details — this is always up-to-date for both
  // reference and submission views. criterion.score may be stale from a previous
  // grading run and must not override the correctly-fetched groupDetails.
  if (groupDetails.value?.earned_points !== null && groupDetails.value?.earned_points !== undefined) {
    return groupDetails.value.earned_points;
  }
  // Fallback: criterion itself may carry earned_points (embedded from grading response)
  if ((props.criterion as any).earned_points !== null && (props.criterion as any).earned_points !== undefined) {
    return (props.criterion as any).earned_points;
  }
  // Last resort: explicit custom score set by the user
  if (props.criterion.score !== null && props.criterion.score !== undefined) {
    return props.criterion.score;
  }
  return 0;
});

const bestRuleName = computed(() => {
  if (!groupDetails.value?.best_rule_id || !groupDetails.value?.rule_results) {
    return undefined;
  }
  const bestRule = groupDetails.value.rule_results.find(t => t.rule_id === groupDetails.value?.best_rule_id);
  return bestRule ? `Max points derived from rule: ${bestRule.rule_name}` : undefined;
});
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
        <p class="text-xs text-gray-500 mt-1">{{ criterion.description }}</p>
      </div>
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
        :class="{'border-l-4 border-l-yellow-400': isXor && item.id === criterion.best_rule_id}"
        :is-editable="isEditable"
        @edit="emit('editCriterion', { check_complexity: CheckComplexity.COMPLEX, ...item })"
        @click="emit('toggleHighlight', -1, item.problematic_elements)" 
      />
      <!-- Note: ToggleHighlight index -1 is a placeholder... -->
    </div>
  </div>
</template>
