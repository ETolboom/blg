<script lang="ts" setup>
import {FunctionalComponent} from "vue";

withDefaults(defineProps<{
  icon: FunctionalComponent;
  as?: string;
}>(), {
  as: 'button'
});

defineEmits<{
  click: [];
}>()

</script>

<template>
  <component
      :is="as"
      class="custom-icon-button"
      @click="$emit('click')">
    <component :is="icon"/>
  </component>
</template>

<style scoped>
.custom-icon-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0.5rem;
  border: 1px solid hsl(225, 10%, 75%);
  border-radius: 6px;
  color: black;
  background-color: #f1f5f9;
  cursor: pointer;
  transition: all 0.2s ease;
  font-size: 1rem;
  text-decoration: none;
}

/* Hover effects */
.custom-icon-button:hover {
  background-color: #e2e8f0;
  border-color: hsl(225, 15%, 65%);
  transform: translateY(-1px);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

/* Active/pressed state */
.custom-icon-button:active {
  background-color: #cbd5e1;
  border-color: hsl(225, 20%, 55%);
  transform: translateY(0);
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
}

/* Focus state for accessibility */
.custom-icon-button:focus-visible {
  outline: 2px solid hsl(225, 70%, 60%);
  outline-offset: 2px;
}
</style>