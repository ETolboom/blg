<script lang="ts" setup>
import {Check, Edit, ExternalLink, Split, XIcon, Trash2} from "lucide-vue-next";
import {computed, ref} from "vue";
import {CheckComplexity} from "@/features/rubric/types/check_complexity.ts";
import type {Criterion} from "@/features/rubric/types/rubric";
import {isGroup as isGroupCriterion} from "@/features/behavior/types/group";

const emit = defineEmits(['toggle', 'reset', 'updatePoints', 'edit', 'delete']);

const props = withDefaults(defineProps<{
  title?: string;
  description?: string;
  state?: boolean | null;
  points?: number;
  custom_score_set?: boolean;
  category?: CheckComplexity;
  criterion?: Criterion;
  isEditable?: boolean;
}>(), {
  isEditable: true
});

// Canonical "is this a group" predicate: the `group:` id prefix (see group.ts),
// not the condition field, so it agrees with RubricSidebar's routing.
const isGroup = computed(() => isGroupCriterion(props.criterion ?? {}));

const expanded = ref(false);

const toggleExpand = () => {
  expanded.value = !expanded.value;
};


const editing = ref(false);
const draft = ref(props.points);

function startEdit() {
  editing.value = true;
  draft.value = props.points;
  setTimeout(() => (document.getElementById('points-input') as HTMLInputElement)?.select(), 0);
}

function finishEdit() {
  editing.value = false;
  emit('updatePoints', draft.value);
}


</script>

<template>
  <div class="flex flex-col bg-white border min-h-28 h-auto w-full px-2 rounded-md shadow-sm transition-all duration-200">
    <div class="flex flex-row h-28 w-full">
    <div class="flex flex-col justify-center items-center py-2">
      <template v-if="state === null">
        <div class="bg-yellow-600 cursor-pointer flex justify-center items-center h-16 w-16 rounded-t-sm">
          <span class="text-3xl">?</span>
        </div>
        <p class="bg-gray-50 text-gray-700 border border-gray-200 w-full h-8 flex justify-center items-center font-semibold rounded-b-sm">
          {{ props.points }}</p>
      </template>
      <template v-else-if="state">
        <div v-if="custom_score_set"
             class="bg-orange-400 text-white cursor-pointer flex justify-center items-center h-16 w-16 rounded-t-sm"
             @click.stop="$emit('reset')">
          <Split :size="36"/>
        </div>
        <div v-else
             class="bg-green-600 text-white cursor-pointer flex justify-center items-center h-16 w-16 rounded-t-sm"
             @click.stop="$emit('toggle')">
          <Check :size="36"/>
        </div>
        <input
            v-if="editing"
            id="points-input"
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
      </template>
      <template v-else-if="!state">
        <div class="bg-red-600 text-white cursor-pointer flex justify-center items-center h-16 w-16 rounded-t-sm"
             @click.stop="$emit('toggle')">
          <XIcon :size="36"/>
        </div>
        <input
            v-if="editing"
            id="points-input"
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
          {{ props.points }}</p>
      </template>
    </div>
    <div class="my-2 bg-gray-50 border border-gray-200 rounded-sm flex-1 ml-2 p-2 flex flex-col relative">
      <div class="flex items-center gap-2 pb-2">
        <span class="font-semibold uppercase text-md text-gray-800">{{ title }}</span>
        <span v-if="props.criterion?.condition === 'XOR'" class="bg-blue-500 text-white text-xs font-bold px-1.5 py-0.5 rounded">XOR</span>
        <span v-if="props.criterion?.condition === 'AND'" class="bg-green-500 text-white text-xs font-bold px-1.5 py-0.5 rounded">AND</span>
      </div>
      <div class="flex flex-col flex-1 mr-8">
        <p class="text-gray-600 text-sm flex-1">{{ description }}</p>
      </div>
      <div class="flex items-center pr-2 absolute right-0">
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