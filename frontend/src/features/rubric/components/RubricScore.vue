<script lang="ts" setup>
interface RubricScoreProps {
  correctScore: number;
  totalScore: number;
  correctPercentage: string;
}

defineProps<RubricScoreProps>();
</script>

<template>
  <div class="bg-white border-t border-gray-200 p-4 rounded-t-lg mx-1 shadow">
    <div class="flex items-center justify-between">
      <span class="text-gray-600 font-medium">Score</span>
      <div class="flex items-center gap-2">
        <span class="text-2xl font-bold text-gray-800">{{ correctScore.toFixed(2).toString() }} / {{ totalScore.toFixed(2).toString() }}</span>
        <span class="text-black font-semibold">({{ correctPercentage }}%)</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
</style>
