<script lang="ts" setup>
import {useNode} from '@vue-flow/core'
import {computed, ref} from 'vue'
import type {NoteNodeProps} from '../../types/nodes.ts'
import NodeDeleteButton from './NodeDeleteButton.vue'

const props = defineProps<NoteNodeProps>();

const {node} = useNode();

const noteText = computed<string>({
  get: () => props.data.noteText ?? '',
  set: (value: string) => {
    node.data.noteText = value
  }
});

const isEditingLabel = ref<boolean>(false);
const editingLabelValue = ref<string>('');
const labelInputRef = ref<HTMLInputElement | null>(null);

const label = computed(() => props.data.label ?? 'Note');
const flagged = computed(() => props.data.flagged ?? false);
const borderColor = computed(() => flagged.value ? '#ef4444' : '#fbbf24');

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
    event.preventDefault();
    editingLabelValue.value = label.value;
    isEditingLabel.value = false
  }
}
</script>

<template>
  <div
      :style="{ borderColor: borderColor }"
      class="p-3 rounded-lg border-2 bg-yellow-50 min-w-[200px] max-w-[300px] shadow-md transition-all duration-200 hover:shadow-lg hover:-translate-y-0.5 relative">
    <NodeDeleteButton :node-id="node.id"/>
    <div class="mb-2">
      <div
          v-if="!isEditingLabel"
          class="text-sm font-semibold text-amber-900 cursor-pointer px-1 py-0.5 rounded-sm transition-colors hover:bg-amber-100" title="Double-click to edit" @dblclick="startEditingLabel">
        {{ label }}
      </div>
      <input
          v-else
          ref="labelInputRef"
          v-model="editingLabelValue"
          class="text-sm font-semibold text-amber-900 px-1 py-0.5 border-2 border-amber-400 rounded-sm outline-none w-full font-[inherit] bg-white box-border"
          type="text"
          @blur="finishEditingLabel"
          @keydown="handleLabelKeydown"
      />
    </div>

    <textarea
        v-model="noteText"
        class="w-full min-h-[80px] p-2 text-[13px] font-[inherit] text-amber-900 bg-white border-2 border-amber-200 rounded resize-y transition-colors box-border hover:border-amber-400 focus:outline-none focus:border-amber-500 placeholder:text-amber-600 placeholder:opacity-50"
        placeholder="Add your notes here..."
        rows="5"
    ></textarea>
  </div>
</template>
