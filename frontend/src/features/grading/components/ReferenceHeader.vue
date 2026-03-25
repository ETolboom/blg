<script lang="ts" setup>
import {Save, RotateCcw, Loader2, RefreshCw} from "lucide-vue-next";
import {computed} from "vue";

const props = defineProps<{
  hasChanges: boolean;
  isSaving: boolean;
  isRegrading: boolean;
}>();

defineEmits<{
  save: [];
  clear: [];
}>();

const clearDisabled = computed(() => !props.hasChanges || props.isSaving);
const saveDisabled = computed(() => !props.hasChanges || props.isSaving || props.isRegrading);
const saveIcon = computed(() => props.isRegrading ? RefreshCw : props.isSaving ? Loader2 : Save);
const saveTooltip = computed(() => props.isRegrading ? 'Re-grading submission…' : props.isSaving ? 'Saving…' : 'Save changes');
</script>

<template>
  <div class="absolute z-10 flex flex-col justify-center items-center py-2 bottom-56 right-4 w-[48px]"
       style="border-radius: 2px; border: solid 1px hsl(225, 10%, 75%); background-color: rgb(247, 247, 248);">
    <RotateCcw
        v-tooltip.left="'Discard changes'"
        :size="32"
        class="my-1 cursor-pointer"
        :class="{ 'opacity-40 cursor-not-allowed pointer-events-none': clearDisabled }"
        color="black"
        @click="!clearDisabled && $emit('clear')"/>
    <span class="w-8/12 bg-gray-400" style="height: 1px; margin: 5px;"/>
    <component
        :is="saveIcon"
        v-tooltip.left="saveTooltip"
        :size="32"
        class="my-1 cursor-pointer"
        :class="{ 'opacity-40 cursor-not-allowed pointer-events-none': saveDisabled }"
        color="black"
        @click="!saveDisabled && $emit('save')"/>
  </div>
</template>
