<script lang="ts" setup>
import {Handle, Position, useNode} from '@vue-flow/core'
import {computed} from 'vue'
import type {EndNodeProps} from '../../types/nodes.ts'
import NodeDeleteButton from './NodeDeleteButton.vue'

const props = defineProps<EndNodeProps>();

const {node} = useNode();

const label = computed(() => props.data.label ?? 'End');
const flagged = computed(() => props.data.flagged ?? false);
const borderColor = computed(() => flagged.value ? '#ef4444' : '#dc2626')
</script>

<template>
  <div
      :style="{
    borderColor: borderColor,
    background: 'linear-gradient(135deg, #fee2e2 0%, #fecaca 100%)',
    boxShadow: flagged ? '0 4px 12px rgba(220, 38, 38, 0.3)' : '0 2px 8px rgba(220, 38, 38, 0.2)'
  }"
      class="py-3 px-4 rounded-lg border-3 min-w-[80px] transition-all duration-200 flex flex-col items-center gap-1 relative hover:-translate-y-0.5">
    <NodeDeleteButton :node-id="node.id"/>
    <Handle id="input" :position="Position.Left" type="target"/>
    <div class="text-2xl text-red-600 font-bold leading-none">■</div>
    <div class="text-xs font-semibold text-red-900 uppercase tracking-wide">{{ label }}</div>
  </div>
</template>
