<script lang="ts" setup>
import {Crosshair, ZoomIn, ZoomOut} from "lucide-vue-next";
import type BpmnModeler from "bpmn-js/lib/Modeler";

const props = defineProps<{
  modeler: BpmnModeler
}>();

const zoomIn = () => props.modeler.get('zoomScroll').stepZoom(1);
const zoomOut = () => props.modeler.get('zoomScroll').stepZoom(-1);
const resetZoom = () => props.modeler.get('zoomScroll').reset();

</script>

<template>
  <div class="absolute z-10 flex flex-col justify-center items-center py-2 bottom-12 right-4 w-[48px]"
       style="border-radius: 2px; border: solid 1px hsl(225, 10%, 75%); background-color: hsl(225, 10%, 97%)">
    <Crosshair :size="32" class="my-1 cursor-pointer" color="black" @click="resetZoom"/>
    <span class="w-8/12 bg-gray-400" style="height: 1px; margin: 5px;"/>
    <ZoomIn :size="32" class="my-1 cursor-pointer" color="black" @click="zoomIn"/>
    <span class="w-8/12 bg-gray-400" style="height: 1px; margin: 5px;"/>
    <ZoomOut :size="32" class="my-1 cursor-pointer" color="black" @click="zoomOut"/>
  </div>
</template>