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
    problematic_elements: result.match_details?.map(m => m.bpmn_element_id) || []
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
        :class="{'border-l-4 border-l-yellow-400': isXor && item.id === bestRuleId}"
        :is-editable="isEditable"
        @edit="emit('editCriterion', { check_complexity: CheckComplexity.COMPLEX, ...item })"
        @click="emit('toggleHighlight', -1, item.problematic_elements)" 
      />
      <!-- Note: ToggleHighlight index -1 is a placeholder... -->
    </div>
  </div>
</template>
