<script lang="ts" setup>
import type {Edge, Node} from '@vue-flow/core'
import {Handle, Position, useNode, useVueFlow} from '@vue-flow/core'
import {computed, inject} from 'vue'
import type {CheckNodeData, CheckNodeProps, RelationshipConnectorData} from '../../types/nodes.ts'
import {getDefaultNodeData, NODE_TYPES} from '../../types/nodeRegistry.ts'
import type {NodeValidationState} from '../../types/validation'
import ScoreControl from './ScoreControl.vue'
import NodeDeleteButton from './NodeDeleteButton.vue'

const props = defineProps<CheckNodeProps>();

const {node} = useNode();
const {addNodes, removeNodes, addEdges} = useVueFlow();

// Inject validation state from parent
const getNodeValidationState = inject<(nodeId: string) => NodeValidationState | undefined>('getNodeValidationState', () => undefined);

const validationState = computed(() => getNodeValidationState(node.id));

const validationBorderColor = computed(() => {
  if (!validationState.value) return 'border-yellow-400';

  switch (validationState.value.validationStatus) {
    case 'perfect':
      return 'border-green-500 border-4';
    case 'good-wrong-position':
      return 'border-yellow-500 border-4';
    case 'acceptable-not-ideal':
      return 'border-orange-500 border-4';
    case 'incorrect':
      return 'border-red-500 border-4';
    default:
      return 'border-yellow-400';
  }
});

const validationTooltip = computed(() => {
  const match = validationState.value?.matchDetail;
  if (!match) return '';

  const lines = [
    `BPMN: ${match.bpmn_label}`,
    `Match Confidence: ${match.match_score.toFixed(2)} (min: ${match.minimal_match_threshold}, ideal: ${match.ideal_match_threshold})`,
    `Distance: ${match.distance} (ideal: ${match.ideal_distance})`,
    '',
    match.is_correct ? '✓ Above minimal threshold' : '✗ Below minimal threshold',
    match.is_ideal_match ? '✓ Above ideal threshold' : '⚠ Below ideal threshold',
    match.is_ideal_distance ? '✓ At ideal distance' : '⚠ Not at ideal distance'
  ];

  return lines.join('\n');
});

const score = computed<number>({
  get: () => props.data.points ?? 0,
  set: (value: number) => {
    node.data.points = value
  }
});

const checkType = computed(() => props.data.checkType ?? 'Element');
const flagged = computed(() => props.data.flagged ?? false);

const gatewayType = computed<string>({
  get: () => props.data.gatewayType ?? 'event',
  set: (value: string) => {
    node.data.gatewayType = value;
    if (!checkLabel_enabled.value) {
      updateGenericGatewayLabel();
    }
  }
});

const gatewayOutcomes = computed<string[]>({
  get: () => props.data.gatewayOutcomes ?? [],
  set: (value: string[]) => {
    node.data.gatewayOutcomes = value
  }
});

const checkLabel = computed<string>({
  get: () => props.data.label ?? '',
  set: (value: string) => {
    node.data.label = value;
  }
});

const elementType = computed<string>({
  get: () => props.data.elementType ?? 'task',
  set: (value: string) => {
    node.data.elementType = value
  }
});

const dataType = computed<string>({
  get: () => props.data.dataType ?? 'Data Object',
  set: (value: string) => {
    node.data.dataType = value
  }
});

const eventType = computed<string>({
  get: () => props.data.eventType ?? 'Message Event',
  set: (value: string) => {
    node.data.eventType = value
  }
});

const eventPosition = computed<string>({
  get: () => props.data.eventPosition ?? 'Start',
  set: (value: string) => {
    node.data.eventPosition = value
  }
});

const eventBehavior = computed<string>({
  get: () => props.data.eventBehavior ?? 'Catch',
  set: (value: string) => {
    node.data.eventBehavior = value
  }
});

const isInterrupting = computed<string>({
  get: () => props.data.isInterrupting ?? 'Interrupting',
  set: (value: string) => {
    node.data.isInterrupting = value
  }
});

const hasBoundaryEvent = computed<boolean>({
  get: () => props.data.hasBoundaryEvent ?? false,
  set: (value: boolean) => {
    node.data.hasBoundaryEvent = value;
    if (value && !node.data.boundaryEventNodeId) {
      createBoundaryEventNode()
    } else if (!value && node.data.boundaryEventNodeId) {
      removeBoundaryEventNode()
    }
  }
});

const isGatewayCheck = computed(() => checkType.value === 'gateway');
const isElementCheck = computed(() => checkType.value === 'element');

const checkLabel_enabled = computed<boolean>({
  get: () => props.data.isGatewayChecked ?? false,
  set: (value: boolean) => {
    node.data.isGatewayChecked = value;
    // Update label to generic when unchecked
    if (!value) {
      updateGenericGatewayLabel();
    }
  }
});

const checkOutcome_enabled = computed<boolean>({
  get: () => props.data.isOutcomeChecked ?? false,
  set: (value: boolean) => {
    node.data.isOutcomeChecked = value;
    // Update outcomes to generic when unchecked
    if (!value) {
      updateGenericOutcomeLabels();
    }
  }
});


function getGenericGatewayLabel(type: string): string {
  switch (type) {
    case 'xor':
      return 'XOR Gateway';
    case 'event':
      return 'Event Gateway';
    case 'parallel':
      return 'Parallel Gateway';
    default:
      return 'Gateway';
  }
}

function updateGenericGatewayLabel(): void {
  checkLabel.value = getGenericGatewayLabel(gatewayType.value);
}

function updateGenericOutcomeLabels(): void {
  // Update all outcomes to generic labels (empty strings)
  gatewayOutcomes.value = gatewayOutcomes.value.map(() => '');
}

const isDataElement = computed(() => isElementCheck.value && elementType.value === 'data');
const isEventElement = computed(() => isElementCheck.value && elementType.value === 'event');
const isAbstractEvent = computed(() => isEventElement.value && eventType.value === 'Abstract Event');
const isIntermediateEvent = computed(() => isEventElement.value && eventPosition.value === 'Intermediate');
const isBoundaryEvent = computed(() => isIntermediateEvent.value && eventBehavior.value === 'Boundary');

function addOutcome(): void {
  gatewayOutcomes.value = [...gatewayOutcomes.value, ''];
}

function removeOutcome(index: number): void {
  gatewayOutcomes.value = gatewayOutcomes.value.filter((_, i) => i !== index)
}

function updateOutcomeLabel(index: number, value: string): void {
  const updated = [...gatewayOutcomes.value];
  updated[index] = value;
  gatewayOutcomes.value = updated;
}

let boundaryEventNodeIdCounter = 0;

function createBoundaryEventNode(): void {
  const timestamp = Date.now();
  const counter = boundaryEventNodeIdCounter++;

  const followedByNodeId = `${node.id}_followed_by_${timestamp}_${counter}`;
  const boundaryNodeId = `${node.id}_boundary_${timestamp}_${counter}`;

  // Create the "followed by" connector node
  const followedByData = getDefaultNodeData(NODE_TYPES.FOLLOWED_BY) as RelationshipConnectorData;
  const followedByNode: Node = {
    id: followedByNodeId,
    type: NODE_TYPES.FOLLOWED_BY,
    position: {
      x: node.position.x + 200,
      y: node.position.y
    },
    data: followedByData
  };

  // Create the boundary event element check node
  const boundaryData = getDefaultNodeData(NODE_TYPES.ELEMENT_CHECK) as CheckNodeData;
  const boundaryNode: Node = {
    id: boundaryNodeId,
    type: NODE_TYPES.ELEMENT_CHECK,
    position: {
      x: node.position.x + 400,
      y: node.position.y
    },
    data: {
      ...boundaryData,
      label: 'Boundary Event',
      elementType: 'event',
      eventType: 'Error Event',
      eventPosition: 'Intermediate',
      eventBehavior: 'Boundary',
      isInterrupting: 'Interrupting',
      parentNodeId: node.id
    }
  };

  // Create edges: element check -> followed by -> boundary event element check
  const edge1: Edge = {
    id: `${node.id}-${followedByNodeId}`,
    source: node.id,
    target: followedByNodeId
  };

  const edge2: Edge = {
    id: `${followedByNodeId}-${boundaryNodeId}`,
    source: followedByNodeId,
    target: boundaryNodeId
  };

  addNodes([followedByNode, boundaryNode]);
  addEdges([edge1, edge2]);

  // Store the node IDs in the parent
  node.data.boundaryFollowedByNodeId = followedByNodeId;
  node.data.boundaryEventNodeId = boundaryNodeId
}

function removeBoundaryEventNode(): void {
  const nodesToRemove: string[] = [];

  if (node.data.boundaryFollowedByNodeId) {
    nodesToRemove.push(node.data.boundaryFollowedByNodeId);
    node.data.boundaryFollowedByNodeId = null
  }

  if (node.data.boundaryEventNodeId) {
    nodesToRemove.push(node.data.boundaryEventNodeId);
    node.data.boundaryEventNodeId = null
  }

  if (nodesToRemove.length > 0) {
    removeNodes(nodesToRemove)
  }
}
</script>

<template>
  <div
      :class="['p-3 rounded-lg border-3 bg-white min-w-[150px] shadow-md transition-all duration-200 hover:shadow-lg hover:-translate-y-0.5 check-node relative', validationBorderColor, flagged ? 'flagged-node' : '']"
      :title="validationTooltip">
    <NodeDeleteButton :node-id="node.id"/>
    <Handle id="input" :position="Position.Left" type="target"/>
    <div v-if="isGatewayCheck" class="mt-2 mb-2 p-2 bg-slate-50 rounded flex flex-col gap-3">
      <div class="flex flex-col gap-1">
        <label class="block text-[11px] font-semibold text-slate-500 uppercase tracking-wide">Gateway Type:</label>
        <select v-model="gatewayType"
                class="w-full px-2 py-1 text-xs font-medium text-slate-800 bg-white border-2 border-slate-300 rounded cursor-pointer font-[inherit] transition-colors hover:border-slate-400 focus:outline-none focus:border-blue-500">
          <option value="event">Event Gateway</option>
          <option value="xor">XOR Gateway</option>
          <option value="parallel">Parallel Gateway</option>
        </select>
      </div>
      <div class="flex flex-col gap-1">
        <label class="block text-[11px] font-semibold text-slate-500 uppercase tracking-wide">Gateway Label:</label>
        <input
            v-if="checkLabel_enabled"
            v-model="checkLabel"
            class="w-full px-2 py-1 text-xs font-medium text-slate-800 bg-white border-2 border-slate-300 rounded font-[inherit] transition-colors hover:border-slate-400 focus:outline-none focus:border-blue-500 placeholder:text-slate-400"
            placeholder="Enter gateway label"
            type="text"
        />
        <div v-else
             class="px-2 py-1 text-xs font-medium text-slate-500 bg-slate-100 border-2 border-slate-300 rounded italic">
          {{ checkLabel }}
        </div>
      </div>
      <div class="flex flex-col gap-2 pt-2 border-t-2 border-slate-200">
        <label class="block text-[10px] font-bold text-slate-400 uppercase tracking-wider">Options</label>
        <div class="grid grid-cols-2 gap-2">
          <label
              class="flex flex-col items-center justify-center cursor-pointer px-2 py-2 rounded border-2 border-slate-200 transition-colors hover:bg-slate-100 hover:border-slate-300">
            <input v-model="checkLabel_enabled" class="cursor-pointer w-4 h-4 accent-blue-500 mb-1" type="checkbox"/>
            <span class="text-[10px] font-medium text-slate-700 text-center leading-tight">Check Gateway Label</span>
          </label>
          <label
              class="flex flex-col items-center justify-center cursor-pointer px-2 py-2 rounded border-2 border-slate-200 transition-colors hover:bg-slate-100 hover:border-slate-300">
            <input v-model="checkOutcome_enabled" class="cursor-pointer w-4 h-4 accent-blue-500 mb-1" type="checkbox"/>
            <span class="text-[10px] font-medium text-slate-700 text-center leading-tight">Check Outcome Labels</span>
          </label>
        </div>
      </div>
      <div class="flex flex-col gap-2 pt-2 border-t-2 border-slate-200">
        <div class="flex items-center justify-between">
          <label class="block text-[11px] font-semibold text-slate-500 uppercase tracking-wide">Outcomes</label>
          <button
              class="px-2 py-1 bg-emerald-500 text-white border-none rounded text-xs font-bold cursor-pointer transition-colors hover:bg-emerald-600"
              type="button"
              @click="addOutcome">+ Add Outcome
          </button>
        </div>
        <div v-if="gatewayOutcomes.length > 0" class="flex flex-col gap-1">
          <div v-for="(outcome, index) in gatewayOutcomes" :key="index"
               class="flex items-center gap-2">
            <span class="text-[10px] font-semibold text-slate-400 w-16">Outcome {{ index + 1 }}:</span>
            <input
                v-if="checkOutcome_enabled"
                :value="outcome"
                class="flex-1 px-2 py-1 text-xs font-medium text-slate-800 bg-white border-2 border-slate-300 rounded font-[inherit] transition-colors hover:border-slate-400 focus:outline-none focus:border-blue-500 placeholder:text-slate-400"
                placeholder="Enter outcome label"
                type="text"
                @input="(e) => updateOutcomeLabel(index, (e.target as HTMLInputElement).value)"
            />
            <div v-else
                 class="flex-1 px-2 py-1 text-xs font-medium text-slate-500 bg-slate-100 border-2 border-slate-300 rounded italic">
              {{ outcome || `Outcome ${index + 1}` }}
            </div>
            <button
                class="bg-transparent border-none text-red-500 text-lg font-bold cursor-pointer px-1 leading-none transition-colors hover:text-red-600"
                type="button"
                @click="removeOutcome(index)">×
            </button>
          </div>
        </div>
      </div>
    </div>
    <div v-if="isElementCheck" class="mt-2 mb-2 p-2 bg-slate-50 rounded flex flex-col gap-2">
      <div class="flex flex-col gap-1">
        <label class="block text-[11px] font-justify-aroundsemibold text-slate-500 uppercase tracking-wide">Element Label:</label>
        <input
            v-model="checkLabel"
            class="w-full px-2 py-1 text-xs font-medium text-slate-800 bg-white border-2 border-slate-300 rounded font-[inherit] transition-colors hover:border-slate-400 focus:outline-none focus:border-blue-500 placeholder:text-slate-400"
            placeholder="Enter element label"
            type="text"
        />
      </div>
      <div class="flex flex-col gap-1">
        <label class="block text-[11px] font-semibold text-slate-500 uppercase tracking-wide">Element Type:</label>
        <select v-model="elementType"
                class="w-full px-2 py-1 text-xs font-medium text-slate-800 bg-white border-2 border-slate-300 rounded cursor-pointer font-[inherit] transition-colors hover:border-slate-400 focus:outline-none focus:border-blue-500">
          <option value="task">Task</option>
          <option value="data">Data</option>
          <option value="event">Event</option>
        </select>
      </div>
      <div v-if="isDataElement" class="flex flex-col gap-1">
        <label class="block text-[11px] font-semibold text-slate-500 uppercase tracking-wide">Data Type:</label>
        <select v-model="dataType"
                class="w-full px-2 py-1 text-xs font-medium text-slate-800 bg-white border-2 border-slate-300 rounded cursor-pointer font-[inherit] transition-colors hover:border-slate-400 focus:outline-none focus:border-blue-500">
          <option value="Data Object">Data Object</option>
          <option value="Data Store">Data Store</option>
        </select>
      </div>
      <template v-if="isEventElement">
        <div class="flex flex-col gap-1">
          <label class="block text-[11px] font-semibold text-slate-500 uppercase tracking-wide">Event Type:</label>
          <select v-model="eventType"
                  class="w-full px-2 py-1 text-xs font-medium text-slate-800 bg-white border-2 border-slate-300 rounded cursor-pointer font-[inherit] transition-colors hover:border-slate-400 focus:outline-none focus:border-blue-500">
            <option value="Abstract Event">Abstract Event</option>
            <option value="Message Event">Message Event</option>
            <option value="Timer Event">Timer Event</option>
            <option value="Error Event">Error Event</option>
          </select>
        </div>
        <div class="flex flex-col gap-1">
          <label class="block text-[11px] font-semibold text-slate-500 uppercase tracking-wide">Event Position:</label>
          <div class="flex gap-2 py-1">
            <label
                class="flex items-center gap-1 cursor-pointer px-2 py-1 rounded transition-colors hover:bg-slate-100">
              <input v-model="eventPosition" class="cursor-pointer w-4 h-4 accent-blue-500" type="radio" value="Start"/>
              <span class="text-xs font-medium text-slate-800 select-none">Start</span>
            </label>
            <label
                class="flex items-center gap-1 cursor-pointer px-2 py-1 rounded transition-colors hover:bg-slate-100">
              <input v-model="eventPosition" class="cursor-pointer w-4 h-4 accent-blue-500" type="radio"
                     value="Intermediate"/>
              <span class="text-xs font-medium text-slate-800 select-none">Intermediate</span>
            </label>
            <label
                class="flex items-center gap-1 cursor-pointer px-2 py-1 rounded transition-colors hover:bg-slate-100">
              <input v-model="eventPosition" class="cursor-pointer w-4 h-4 accent-blue-500" type="radio" value="End"/>
              <span class="text-xs font-medium text-slate-800 select-none">End</span>
            </label>
          </div>
        </div>
        <div v-if="isIntermediateEvent && !isAbstractEvent" class="flex flex-col gap-1">
          <label class="block text-[11px] font-semibold text-slate-500 uppercase tracking-wide">Event Behavior:</label>
          <div class="flex gap-2 py-1">
            <label
                class="flex items-center gap-1 cursor-pointer px-2 py-1 rounded transition-colors hover:bg-slate-100">
              <input v-model="eventBehavior" class="cursor-pointer w-4 h-4 accent-blue-500" type="radio" value="Catch"/>
              <span class="text-xs font-medium text-slate-800 select-none">Catch</span>
            </label>
            <label
                class="flex items-center gap-1 cursor-pointer px-2 py-1 rounded transition-colors hover:bg-slate-100">
              <input v-model="eventBehavior" class="cursor-pointer w-4 h-4 accent-blue-500" type="radio"
                     value="Boundary"/>
              <span class="text-xs font-medium text-slate-800 select-none">Boundary</span>
            </label>
            <label
                class="flex items-center gap-1 cursor-pointer px-2 py-1 rounded transition-colors hover:bg-slate-100">
              <input v-model="eventBehavior" class="cursor-pointer w-4 h-4 accent-blue-500" type="radio" value="Throw"/>
              <span class="text-xs font-medium text-slate-800 select-none">Throw</span>
            </label>
          </div>
        </div>
        <div v-if="isBoundaryEvent" class="flex flex-col gap-1">
          <label class="block text-[11px] font-semibold text-slate-500 uppercase tracking-wide">Interrupting:</label>
          <div class="flex gap-2 py-1">
            <label
                class="flex items-center gap-1 cursor-pointer px-2 py-1 rounded transition-colors hover:bg-slate-100">
              <input v-model="isInterrupting" class="cursor-pointer w-4 h-4 accent-blue-500" type="radio"
                     value="Interrupting"/>
              <span class="text-xs font-medium text-slate-800 select-none">Interrupting</span>
            </label>
            <label
                class="flex items-center gap-1 cursor-pointer px-2 py-1 rounded transition-colors hover:bg-slate-100">
              <input v-model="isInterrupting" class="cursor-pointer w-4 h-4 accent-blue-500" type="radio"
                     value="Non-Interrupting"/>
              <span class="text-xs font-medium text-slate-800 select-none">Non-Interrupting</span>
            </label>
          </div>
        </div>
      </template>
      <div v-if="!isBoundaryEvent" class="flex flex-col gap-1">
        <label class="block text-[11px] font-semibold text-slate-500 uppercase tracking-wide">Has Boundary
          Event:</label>
        <div class="flex gap-2 py-1">
          <label class="flex items-center gap-1 cursor-pointer px-2 py-1 rounded transition-colors hover:bg-slate-100">
            <input v-model="hasBoundaryEvent" class="cursor-pointer w-4 h-4 accent-blue-500" type="checkbox"/>
            <span class="text-xs font-medium text-slate-800 select-none">{{ hasBoundaryEvent ? 'Yes' : 'No' }}</span>
          </label>
        </div>
      </div>
    </div>
    <div class="flex flex-col gap-1.5">
      <div class="mt-2 flex flex-col gap-1">
        <label class="text-[11px] font-semibold text-slate-500 uppercase tracking-wide">Score:</label>
        <ScoreControl v-model="score"/>
      </div>
    </div>
    <template v-if="isGatewayCheck && gatewayOutcomes.length > 0">
      <Handle
          v-for="(outcome, index) in gatewayOutcomes"
          :id="`outcome-${index}`"
          :key="`outcome-${index}`"
          :position="Position.Right"
          :style="{ top: `${((index + 1) * 100) / (gatewayOutcomes.length + 1)}%` }"
          type="source"
      >
        <span
            class="absolute right-full mr-2 text-[11px] font-semibold text-slate-500 whitespace-nowrap bg-white px-1.5 py-0.5 rounded-sm border border-slate-300 pointer-events-none">{{
            outcome || `Outcome ${index + 1}`
          }}</span>
      </Handle>
    </template>
    <Handle
        v-else
        id="output"
        :position="Position.Right"
        type="source"
    />
  </div>
</template>

<style scoped>
.check-node {
  border-width: 2px;
  border-style: solid;
  transition: border-color 0.3s ease;
}

.flagged-node {
  animation: pulse-red 1.5s ease-in-out infinite;
}

@keyframes pulse-red {
  0%, 100% {
    box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.7);
  }
  50% {
    box-shadow: 0 0 0 10px rgba(239, 68, 68, 0);
  }
}
</style>