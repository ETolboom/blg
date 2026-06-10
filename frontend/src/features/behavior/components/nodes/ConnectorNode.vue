<script lang="ts" setup>
import {Handle, Position, useNode} from '@vue-flow/core'
import {computed, ref} from 'vue'
import type {ConnectorNodeProps} from '../../types/nodes.ts'
import {NODE_TYPES} from "../../types/nodeRegistry.ts";
import NodeDeleteButton from './NodeDeleteButton.vue'

const props = defineProps<ConnectorNodeProps>();

const {node} = useNode();

const isEditingLabel = ref<boolean>(false);
const editingLabelValue = ref<string>('');
const labelInputRef = ref<HTMLInputElement | null>(null);

const connectorType = computed(() => props.data.connectorType ?? NODE_TYPES.XOR);
const label = computed(() => props.data.label ?? connectorType.value);
const flagged = computed(() => props.data.flagged ?? false);

interface ConnectorStyle {
  symbol: string
  color: string
  bgColor: string
}

const connectorStyle = computed<ConnectorStyle>(() => {
  if (flagged.value) {
    const baseStyle = getBaseStyle();
    return {
      ...baseStyle,
      color: '#ef4444',
    }
  }

  return getBaseStyle()
});

function getBaseStyle(): ConnectorStyle {
  switch (connectorType.value) {
    case NODE_TYPES.XOR:
      return {
        symbol: 'X',
        color: '#8b5cf6',
        bgColor: '#ede9fe',
      };
    case NODE_TYPES.AND:
      return {
        symbol: '+',
        color: '#10b981',
        bgColor: '#d1fae5',
      };
    default:
      return {
        symbol: '?',
        color: '#6b7280',
        bgColor: '#f3f4f6',
      }
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
    editingLabelValue.value = label.value;
    isEditingLabel.value = false
  }
}
</script>

<template>
  <div
      :style="{
    borderColor: connectorStyle.color,
    backgroundColor: connectorStyle.bgColor
  }"
      class="p-4 rounded-full border-3 bg-white w-[120px] h-[120px] flex flex-col items-center justify-center shadow-md transition-all duration-200 relative hover:shadow-lg hover:scale-105">
    <NodeDeleteButton :node-id="node.id"/>
    <Handle id="input-1" :position="Position.Top" type="target"/>

    <div :style="{ color: connectorStyle.color }" class="text-[28px] font-bold leading-none mb-1">
      {{ connectorStyle.symbol }}
    </div>

    <div class="mt-1 w-full flex justify-center">
      <div
          v-if="!isEditingLabel"
          class="text-[9px] text-slate-500 text-center max-w-full overflow-hidden text-ellipsis whitespace-nowrap cursor-pointer px-1 py-0.5 rounded-sm transition-colors hover:bg-black/5"
          title="Double-click to edit"
          @dblclick="startEditingLabel"
      >
        {{ label }}
      </div>
      <input
          v-else
          ref="labelInputRef"
          v-model="editingLabelValue"
          class="text-[9px] text-slate-800 px-1 py-0.5 border-2 border-blue-500 rounded-sm outline-none w-20 font-[inherit] text-center"
          type="text"
          @blur="finishEditingLabel"
          @keydown="handleLabelKeydown"
      />
    </div>
    <Handle id="input-2" :position="Position.Bottom" type="target"/>
    <Handle id="output" :position="Position.Right" type="source"/>
  </div>
</template>
