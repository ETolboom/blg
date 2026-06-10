<script lang="ts" setup>
import {computed} from 'vue'

const props = defineProps<{
  modelValue: number
}>();

const emit = defineEmits<{
  (e: 'update:modelValue', value: number): void
}>();

const score = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
});

// Round to one decimal so repeated ±0.1 steps don't accumulate IEEE drift
// (e.g. 0.30000000000000004) in the value that gets persisted.
const step = (delta: number): void => {
  score.value = Math.round((props.modelValue + delta) * 10) / 10;
};

</script>

<template>
  <div class="flex items-center justify-center gap-1">
    <button
        class="px-2 py-1 text-xs font-bold bg-white border-2 border-slate-300 rounded cursor-pointer transition-all hover:border-slate-400 hover:bg-slate-50 focus:outline-none focus:border-blue-500"
        type="button"
        @click="step(-1)">
      -1
    </button>
    <button
        class="px-2 py-1 text-xs font-bold bg-white border-2 border-slate-300 rounded cursor-pointer transition-all hover:border-slate-400 hover:bg-slate-50 focus:outline-none focus:border-blue-500"
        type="button"
        @click="step(-0.1)">
      -0.1
    </button>
    <div
        class="px-3 py-1 text-sm font-bold text-slate-800 bg-slate-100 border-2 border-slate-300 rounded min-w-[60px] text-center">
      {{ score.toFixed(1) }}
    </div>
    <button
        class="px-2 py-1 text-xs font-bold bg-white border-2 border-slate-300 rounded cursor-pointer transition-all hover:border-slate-400 hover:bg-slate-50 focus:outline-none focus:border-blue-500"
        type="button"
        @click="step(0.1)">
      +0.1
    </button>
    <button
        class="px-2 py-1 text-xs font-bold bg-white border-2 border-slate-300 rounded cursor-pointer transition-all hover:border-slate-400 hover:bg-slate-50 focus:outline-none focus:border-blue-500"
        type="button"
        @click="step(1)">
      +1
    </button>
  </div>
</template>
