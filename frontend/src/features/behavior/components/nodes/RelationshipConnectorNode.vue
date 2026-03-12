<script lang="ts" setup>
import {Handle, Position, useNode} from '@vue-flow/core'
import {computed, inject, ref} from 'vue'
import type {RelationshipConnectorNodeProps} from '../../types/nodes.ts'
import type {NodeValidationState} from '../../types/validation'
import NodeDeleteButton from './NodeDeleteButton.vue'

const props = defineProps<RelationshipConnectorNodeProps>();

const {node} = useNode();

const isEditingLabel = ref<boolean>(false);
const editingLabelValue = ref<string>('');
const labelInputRef = ref<HTMLInputElement | null>(null);

const label = computed(() => props.data.label ?? 'Followed By');
const flagged = computed(() => props.data.flagged ?? false);

// Inject validation state from parent
const getNodeValidationState = inject<(nodeId: string) => NodeValidationState | undefined>('getNodeValidationState', () => undefined);

const validationState = computed(() => getNodeValidationState(node.id));

const validationBorderColor = computed(() => {
  if (!validationState.value) return 'border-gray-300';

  switch (validationState.value.validationStatus) {
    case 'perfect':
      return 'border-green-500 border-4';
    case 'good-wrong-position':
      return 'border-yellow-500 border-4';
    case 'acceptable-not-ideal':
      return 'border-orange-500 border-4';
    case 'incorrect':
      return 'border-red-500 border-4';
    default:
      return 'border-gray-300';
  }
});

const validationTooltip = computed(() => {
  const match = validationState.value?.matchDetail;
  if (!match) return '';

  const lines = [
    `BPMN: ${match.bpmn_label}`,
    `Match Confidence: ${match.match_score.toFixed(2)}`,
    `(min: ${match.minimal_match_threshold}, ideal: ${match.ideal_match_threshold})`,
    `Distance: ${match.distance} (ideal: ${match.ideal_distance})`
  ];

  return lines.join('\n');
});

const idealDistance = computed<number>({
  get: () => props.data.idealDistance ?? 1,
  set: (value: number) => {
    node.data.idealDistance = value
  }
});

const maxDistance = computed<number>({
  get: () => props.data.maxDistance ?? 2,
  set: (value: number) => {
    node.data.maxDistance = value
  }
});

const showOptions = ref<boolean>(false);

interface RelationshipStyle {
  symbol: string
  color: string
  bgColor: string
}

const relationshipStyle = computed<RelationshipStyle>(() => {
  // If flagged, override with red
  if (flagged.value) {
    const baseStyle = getBaseStyle();
    return {
      ...baseStyle,
      color: '#ef4444',
    }
  }

  return getBaseStyle()
});

function getBaseStyle(): RelationshipStyle {
  return {
    symbol: '→',
    color: '#06b6d4',
    bgColor: '#cffafe',
  }
}

function startEditingLabel(): void {
  isEditingLabel.value = true;
  editingLabelValue.value = label.value;
  setTimeout(() => {
    labelInputRef.value?.focus()
  }, 0)
}

function finishEditingLabel(): void {
  if (editingLabelValue.value.trim()) {
    node.data.label = editingLabelValue.value.trim()
  }
  isEditingLabel.value = false
}

function handleLabelKeydown(event: KeyboardEvent): void {
  if (event.key === 'Enter') {
    event.preventDefault();
    finishEditingLabel()
  } else if (event.key === 'Escape') {
    isEditingLabel.value = false
  }
}

function toggleOptions(): void {
  showOptions.value = !showOptions.value
}
</script>

<template>
  <div
      :class="['py-3 px-4 rounded-lg border-2 bg-white min-w-[160px] flex flex-col shadow-md transition-all duration-200 relative hover:shadow-lg hover:-translate-y-px relationship-node', validationBorderColor]"
      :style="{
    borderColor: validationState ? undefined : relationshipStyle.color,
    backgroundColor: relationshipStyle.bgColor
  }"
      :title="validationTooltip">
    <NodeDeleteButton :node-id="node.id"/>
    <Handle id="input" :position="Position.Left" type="target"/>
    <div class="flex items-center gap-2">
      <div :style="{ color: relationshipStyle.color }" class="text-2xl font-bold leading-none shrink-0">
        {{ relationshipStyle.symbol }}
      </div>
      <div class="flex-1 flex items-center">
        <div
            v-if="!isEditingLabel"
            class="text-xs font-semibold text-slate-800 cursor-pointer px-1.5 py-1 rounded transition-colors whitespace-nowrap hover:bg-black/5"
            title="Double-click to edit"
            @dblclick="startEditingLabel"
        >
          {{ label }}
        </div>
        <input
            v-else
            ref="labelInputRef"
            v-model="editingLabelValue"
            class="text-xs font-semibold text-slate-800 px-1.5 py-1 border-2 border-blue-500 rounded outline-none font-[inherit] w-full"
            type="text"
            @blur="finishEditingLabel"
            @keydown="handleLabelKeydown"
        />
      </div>
      <button
          :class="{ 'bg-blue-500/10 text-blue-500': showOptions }"
          class="bg-black/5 border-none rounded px-2 py-1 text-sm cursor-pointer transition-all shrink-0 hover:bg-black/10"
          title="Toggle options"
          @click="toggleOptions"
      >
        ⚙
      </button>
    </div>
    <div v-if="showOptions" class="bg-black/[0.02] p-2 rounded-md mt-2 flex flex-col gap-1.5">
      <div class="flex items-center justify-between gap-2 text-[11px]">
        <label class="flex items-center gap-1 text-slate-600 font-medium cursor-pointer select-none">Ideal
          Distance:</label>
        <input
            v-model.number="idealDistance"
            class="w-[60px] px-1.5 py-1 border border-slate-300 rounded text-[11px] text-center outline-none transition-colors focus:border-blue-500"
            max="100"
            min="1"
            type="number"
        />
      </div>
      <div class="flex items-center justify-between gap-2 text-[11px]">
        <label class="flex items-center gap-1 text-slate-600 font-medium cursor-pointer select-none">Max
          Distance:</label>
        <input
            v-model.number="maxDistance"
            class="w-[60px] px-1.5 py-1 border border-slate-300 rounded text-[11px] text-center outline-none transition-colors focus:border-blue-500"
            max="100"
            min="1"
            type="number"
        />
      </div>
    </div>
    <Handle id="output" :position="Position.Right" type="source"/>
  </div>
</template>

<style scoped>
.relationship-node {
  border-width: 2px;
  border-style: solid;
  transition: border-color 0.3s ease;
}
</style>
