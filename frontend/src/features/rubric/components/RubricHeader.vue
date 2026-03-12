<script lang="ts" setup>
import {ClipboardList, PanelRightClose, PanelRightOpen} from 'lucide-vue-next';

defineProps<{
  sidebarVisible: Boolean;
}>();

defineEmits<{
  'toggle-sidebar': [];
  'open-menu': [];
}>();


</script>

<template>
  <div
      class="flex items-center justify-between bg-gradient-to-r from-blue-500 to-blue-600 rounded-b-lg px-3 py-3 gap-3">
    <button
        :aria-label="sidebarVisible ? 'Close sidebar' : 'Open sidebar'"
        class="p-2 bg-white/90 hover:bg-white rounded-lg shadow-sm transition-all hover:scale-105 focus:outline-none focus:ring-2 focus:ring-white/50"
        type="button"
        @click="$emit('toggle-sidebar')"
    >
      <PanelRightClose v-if="sidebarVisible" :size="18" class="text-gray-700"/>
      <PanelRightOpen v-else :size="18" class="text-gray-700"/>
    </button>

    <div class="flex-1 flex justify-center">
      <div class="text-white font-semibold text-lg flex items-center gap-2">
        <ClipboardList :size="20"/>
        Rubric
      </div>
    </div>

    <button
        aria-label="Options"
        class="p-2 bg-white/10 hover:bg-white/20 rounded-lg transition-colors"
        type="button"
        @click="$emit('open-menu')"
    >
      <svg fill="none" height="18" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24" width="18">
        <circle cx="12" cy="12" r="1"/>
        <circle cx="12" cy="5" r="1"/>
        <circle cx="12" cy="19" r="1"/>
      </svg>
    </button>
  </div>
</template>


