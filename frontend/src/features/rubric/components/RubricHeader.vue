<script lang="ts" setup>
import {ClipboardList, PanelRightClose, PanelRightOpen} from 'lucide-vue-next';

defineProps<{
  sidebarVisible: Boolean;
}>();

defineEmits<{
  'toggle-sidebar': [];
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

    <!-- Spacer to keep the title centered (options menu removed; see V1_ROADMAP Phase 4.1) -->
    <div class="w-[34px] shrink-0" aria-hidden="true"></div>
  </div>
</template>


