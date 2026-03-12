<script lang="ts" setup>
import {useVueFlow} from '@vue-flow/core'
import {inject} from 'vue'

const props = defineProps<{
  nodeId: string
}>();

const {removeNodes} = useVueFlow();
const isReadOnly = inject('isReadOnly', false);

const removeNode = (event: Event) => {
  event.stopPropagation(); // Prevent selecting the node when clicking delete
  removeNodes([props.nodeId]);
}
</script>

<template>
  <button
      v-if="!isReadOnly"
      class="absolute w-5 h-5 rounded-full flex items-center justify-center text-xs font-bold leading-none cursor-pointer transition-all duration-200 focus:outline-none node-delete-button z-50 -top-2 -right-2 bg-slate-200 text-slate-500 shadow-md hover:bg-red-500 hover:text-white"
      title="Delete Node"
      type="button"
      @click="removeNode"
  >
    ×
  </button>
</template>
