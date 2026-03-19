<script lang="ts" setup>
import {Save, RotateCcw, Loader2, Pencil, RefreshCw} from "lucide-vue-next";
import GradingButton from "@/features/grading/components/GradingButton.vue";

defineProps<{
  hasChanges: boolean;
  isSaving: boolean;
  isRegrading: boolean;
}>();

defineEmits<{
  save: [];
  clear: [];
}>();
</script>

<template>
  <header class="flex relative top-0 flex-row h-14 z-10 p-2 my-2 mx-4 justify-between items-center"
          style="border-radius: 2px; border: solid 1px hsl(225, 10%, 75%); background-color: rgb(247, 247, 248);">
    <div class="flex flex-row gap-x-2 items-center">
      <Pencil class="w-4 h-4 text-gray-500"/>
      <span class="font-semibold text-sm">Reference BPMN</span>
    </div>
    <div class="flex flex-row gap-x-2 items-center">
      <GradingButton v-tooltip.bottom="'Discard changes'" :icon="RotateCcw" :disabled="!hasChanges || isSaving" @click="$emit('clear')"/>
      <GradingButton
          v-tooltip.left="isRegrading ? 'Re-grading submission…' : isSaving ? 'Saving…' : 'Save changes'"
          :icon="isRegrading ? RefreshCw : isSaving ? Loader2 : Save"
          :disabled="!hasChanges || isSaving || isRegrading"
          @click="$emit('save')"/>
    </div>
  </header>
</template>
