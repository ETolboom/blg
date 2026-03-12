<script lang="ts" setup>
import {Handle, Position, useNode} from '@vue-flow/core'
import {computed} from 'vue'
import type {PointsNodeProps} from '../../types/nodes.ts'
import ScoreControl from './ScoreControl.vue'
import NodeDeleteButton from './NodeDeleteButton.vue'

const props = defineProps<PointsNodeProps>();

const {node} = useNode();

const score = computed<number>({
  get: () => props.data.points ?? 0,
  set: (value: number) => {
    node.data.points = value
  }
});

const label = computed(() => props.data.label ?? 'Points');

const borderColor = computed(() => {
  return props.data.borderColor ?? '#cbd5e1'; // Default to slate-300
});
</script>

<template>
  <div
      :style="{ borderColor: borderColor }"
      class="py-3 px-4 rounded-lg border-2 bg-white min-w-[150px] shadow-md transition-all duration-200 relative hover:shadow-lg hover:-translate-y-0.5">
    <NodeDeleteButton :node-id="node.id"/>
    <Handle id="input" :position="Position.Left" type="target"/>
    
    <div class="flex flex-col gap-2">
      <div class="text-xs font-bold text-slate-700 uppercase tracking-wide text-center border-b border-slate-100 pb-1">
        {{ label }}
      </div>
      
      <div class="flex flex-col gap-1">
        <label class="text-[10px] font-semibold text-slate-500 uppercase tracking-wide text-center">Score Modification:</label>
        <ScoreControl v-model="score"/>
      </div>
    </div>

    <Handle id="output" :position="Position.Right" type="source"/>
  </div>
</template>

<style scoped>
.points-node {
  border-color: #cbd5e1; /* slate-300 */
}

.points-node:hover {
  border-color: #94a3b8; /* slate-400 */
}
</style>
