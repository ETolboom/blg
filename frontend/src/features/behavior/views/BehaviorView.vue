<script lang="ts" setup>
import {markRaw, nextTick, onBeforeUnmount, onMounted, onUnmounted, provide, ref, computed, watch} from 'vue'
import {useRoute} from 'vue-router'
import {useToast} from 'primevue'
import Toast from 'primevue/toast'
import type {Connection, Edge, Node} from '@vue-flow/core'
import {useVueFlow, VueFlow} from '@vue-flow/core'
import BehaviorSidebar from '@/features/behavior/components/BehaviorSidebar.vue'
import CheckNode from '@/features/behavior/components/nodes/CheckNode.vue'
import ConnectorNode from '@/features/behavior/components/nodes/ConnectorNode.vue'
import RelationshipConnectorNode from '@/features/behavior/components/nodes/RelationshipConnectorNode.vue'
import EndNode from '@/features/behavior/components/nodes/EndNode.vue'
import NoteNode from '@/features/behavior/components/nodes/NoteNode.vue'
import PointsNode from '@/features/behavior/components/nodes/PointsNode.vue'
import useDragAndDrop from '@/features/behavior/composables/useDragAndDrop.ts'
import {useFlowHistory} from '@/features/behavior/composables/useFlowHistory.ts'
import {Background} from '@vue-flow/background'
import {getDefaultNodeData, isConnectionAllowed, NODE_TYPES, type NodeType} from '@/features/behavior/types/nodeRegistry.ts'
import {ApiError, behavioralRuleService} from "@/services"
import type {ValidationResponse, NodeValidationState} from '@/features/behavior/types/validation'
import type {BehavioralRule} from '@/features/behavior/types/template'

const route = useRoute();
const toast = useToast();

const {onConnect, findNode, addEdges, getEdges, getNodes, addNodes, removeEdges, nodes: vfNodes, edges: vfEdges} = useVueFlow();
const {onDragOver, onDrop, onDragLeave, isDragOver} = useDragAndDrop();

const nodes = ref<Node[]>([]);
const edges = ref<Edge[]>([]);

// New state for rule and validation
const currentRule = ref<BehavioralRule | null>(null);
const validationResults = ref<ValidationResponse | null>(null);
const nodeValidationStates = ref<Map<string, NodeValidationState>>(new Map());
const isValidating = ref<boolean>(false);
const isSaving = ref<boolean>(false);
const hasUnsavedChanges = ref<boolean>(false);
const autoSaveTimeout = ref<ReturnType<typeof setTimeout> | null>(null);
const isLoaded = ref<boolean>(false);
const historyDebounce = ref<ReturnType<typeof setTimeout> | null>(null);

const {isRestoring, canUndo, canRedo, pushState, undo, redo} = useFlowHistory(nodes, edges);

const ruleId = computed(() => route.params.ruleId as string | undefined);
const submissionFilename = computed(() => route.query.submission as string | undefined);
const isReadOnly = computed(() => !!submissionFilename.value);

const nodeTypes = {
  [NODE_TYPES.ELEMENT_CHECK]: markRaw(CheckNode),
  [NODE_TYPES.GATEWAY_CHECK]: markRaw(CheckNode),
  [NODE_TYPES.XOR]: markRaw(ConnectorNode),
  [NODE_TYPES.AND]: markRaw(ConnectorNode),
  [NODE_TYPES.FOLLOWED_BY]: markRaw(RelationshipConnectorNode),
  [NODE_TYPES.END_NODE]: markRaw(EndNode),
  [NODE_TYPES.NOTES_NODE]: markRaw(NoteNode),
  [NODE_TYPES.POINTS_NODE]: markRaw(PointsNode),
};

onConnect((connection: Connection) => {
  const sourceNode = findNode(connection.source);
  const targetNode = findNode(connection.target);

  if (!sourceNode || !targetNode) return false;

  // Valid connection
  if (isConnectionAllowed(sourceNode.type as NodeType, targetNode.type as NodeType)) {
    // Check for existing connections from this source handle
    const existingEdges = getEdges.value.filter(e =>
      e.source === connection.source &&
      e.sourceHandle === connection.sourceHandle
    );

    if (existingEdges.length > 0) {
      // Remove existing edges to enforce single connection per handle
      removeEdges(existingEdges);
    }
    
    addEdges(connection)
    return true;
  }

  // Invalid connection. Need to insert a "Followed By" connector in between.
  // Shift the target node to the right to make room for the connector.
  const gap = 200;
  const midX = (sourceNode.position.x + targetNode.position.x) / 2;
  const midY = (sourceNode.position.y + targetNode.position.y) / 2;

  // Move the target node further right so it doesn't overlap with the connector
  targetNode.position = {
    ...targetNode.position,
    x: Math.max(targetNode.position.x, midX + gap),
  };

  const followedByNode: Node = {
    id: `followedBy-${Date.now()}`,
    type: NODE_TYPES.FOLLOWED_BY,
    position: { x: midX, y: midY },
    data: getDefaultNodeData(NODE_TYPES.FOLLOWED_BY),
  };

  // Add the new connector node
  addNodes([followedByNode]);

  // Create two edges: source -> followedBy -> target
  addEdges([
    {
      id: `${connection.source}-${followedByNode.id}`,
      source: connection.source,
      sourceHandle: connection.sourceHandle,
      target: followedByNode.id,
    },
    {
      id: `${followedByNode.id}-${connection.target}`,
      source: followedByNode.id,
      target: connection.target,
      targetHandle: connection.targetHandle,
    },
  ]);


});

const clearFlow = () => {
  nodes.value = [];
  edges.value = [];
  validationResults.value = null;
  nodeValidationStates.value.clear();
  hasUnsavedChanges.value = true;
};

const runFlow = async () => {
  if (!currentRule.value) {
    toast.add({
      severity: 'error',
      summary: 'No rule loaded',
      detail: 'Cannot validate without a loaded rule'
    });
    return;
  }

  isValidating.value = true;

  try {
    // First, save the current workflow state if not read-only
    if (!isReadOnly.value && hasUnsavedChanges.value) {
      await saveFlow(false);
    }

    // Then validate
    const response = await behavioralRuleService.validateBehavioralRule(currentRule.value.id, submissionFilename.value);
    validationResults.value = response;

    // Process validation results into node states
    processValidationResults(response);

    toast.add({
      severity: 'success',
      summary: 'Validation complete',
      detail: `Confidence: ${(response.validation_result.confidence * 100).toFixed(1)}%`,
      life: 5000
    });

    // Notify about automatically re-evaluated groups
    if (response.affected_groups && response.affected_groups.length > 0) {
      const groupNames = response.affected_groups.map(g => g.group_name).join(', ');
      toast.add({
        severity: 'info',
        summary: 'Groups Updated',
        detail: `The following groups were updated: ${groupNames}`,
        life: 5000
      });
    }

    console.log('Validation results:', response);
  } catch (error) {
    if (error instanceof ApiError) {
      toast.add({
        severity: 'error',
        summary: 'Validation failed',
        detail: error.detail,
        life: 10000
      });
    } else {
      toast.add({
        severity: 'error',
        summary: 'Validation failed',
        detail: String(error),
        life: 10000
      });
    }
    console.error('Validation error:', error);
  } finally {
    isValidating.value = false;
  }
};

const saveFlow = async (showToast: boolean = true) => {
  if (!currentRule.value) {
    toast.add({
      severity: 'error',
      summary: 'No rule loaded',
      detail: 'Cannot save without a loaded rule'
    });
    return;
  }

  isSaving.value = true;

  try {
    const allNodes = normalizeNodes(getNodes.value);
    const allEdges = getEdges.value;

    const updatedRule: BehavioralRule = {
      ...currentRule.value,
      nodes: allNodes,
      edges: allEdges
    };

    // Optimistically mark as clean before async operation.
    // If changes happen *during* the save, the watcher will set it back to true.
    hasUnsavedChanges.value = false;

    await behavioralRuleService.saveBehavioralRule(updatedRule);
    currentRule.value = updatedRule;

    if (showToast) {
      toast.add({
        severity: 'success',
        summary: 'Rule saved',
        detail: `"${currentRule.value.name}" saved successfully`,
        life: 3000
      });
    }
  } catch (error) {
    // If save fails, mark as unsaved again so user knows/auto-save can retry
    hasUnsavedChanges.value = true;
    
    if (error instanceof ApiError) {
      toast.add({
        severity: 'error',
        summary: 'Save failed',
        detail: error.detail,
        life: 10000
      });
    } else {
      toast.add({
        severity: 'error',
        summary: 'Save failed',
        detail: String(error),
        life: 10000
      });
    }
  } finally {
    isSaving.value = false;
  }
};

const processValidationResults = (response: ValidationResponse) => {
  const newStates = new Map<string, NodeValidationState>();

  response.validation_result.match_details.forEach(match => {
    let status: NodeValidationState['validationStatus'];

    if (!match.is_correct) {
      // Below minimal threshold (< 0.6) - incorrect
      status = 'incorrect';
    } else if (match.is_ideal_match && match.is_ideal_distance) {
      // Perfect: score >= 0.8 AND at ideal distance
      status = 'perfect';
    } else if (match.is_ideal_match && !match.is_ideal_distance) {
      // Good match but wrong position: score >= 0.8 BUT not at ideal distance
      status = 'good-wrong-position';
    } else {
      // Acceptable but not ideal: 0.6 <= score < 0.8
      status = 'acceptable-not-ideal';
    }

    newStates.set(match.workflow_node_id, {
      nodeId: match.workflow_node_id,
      matchDetail: match,
      validationStatus: status
    });
  });

  nodeValidationStates.value = newStates;
};

const getNodeValidationState = (nodeId: string): NodeValidationState | undefined => {
  return nodeValidationStates.value.get(nodeId);
};

// Normalize node data to ensure all required fields are present
const normalizeNodes = (nodes: Node[]): Node[] => {
  return nodes.map(node => {
    if (node.type === NODE_TYPES.ELEMENT_CHECK && node.data) {
      const { points: _p, ...rest } = node.data;
      return { ...node, data: rest };
    }
    if (node.type === NODE_TYPES.GATEWAY_CHECK && node.data) {
      const { points: _p, ...rest } = node.data;
      return {
        ...node,
        data: {
          ...rest,
          isGatewayChecked: rest.isGatewayChecked ?? false,
          isOutcomeChecked: rest.isOutcomeChecked ?? false,
        }
      };
    }
    return node;
  });
};



// Track changes to nodes/edges using VueFlow's internal reactive state (not computed getters)
// so that in-place node data mutations (label, type, score, etc.) are detected.
watch([vfNodes, vfEdges], () => {
  if (!isLoaded.value || isReadOnly.value || isRestoring.value) return;

  hasUnsavedChanges.value = true;

  // Debounced history snapshot — captures state after a burst of changes settles
  if (historyDebounce.value) {
    clearTimeout(historyDebounce.value);
  }
  historyDebounce.value = setTimeout(() => {
    pushState();
  }, 500);

  // Auto-save debounce
  if (autoSaveTimeout.value) {
    clearTimeout(autoSaveTimeout.value);
  }

  autoSaveTimeout.value = setTimeout(() => {
    if (hasUnsavedChanges.value && currentRule.value) {
      saveFlow(false);
    }
  }, 5000); // 5s debounce
}, { deep: true });

// Undo / Redo keyboard shortcuts
const onKeyDown = (e: KeyboardEvent) => {
  if (isReadOnly.value) return;
  const modifier = e.metaKey || e.ctrlKey;
  if (!modifier) return;

  if (e.key === 'z' && !e.shiftKey) {
    e.preventDefault();
    undo();
  } else if (e.key === 'y' || (e.key === 'z' && e.shiftKey)) {
    e.preventDefault();
    redo();
  }
};

onMounted(() => {
  window.addEventListener('keydown', onKeyDown);
});
onUnmounted(() => {
  window.removeEventListener('keydown', onKeyDown);
});

onMounted(async () => {
  // Load rule from route parameter
  if (ruleId.value) {
    try {
      currentRule.value = await behavioralRuleService.getBehavioralRule(ruleId.value);
      nodes.value = currentRule.value.nodes || [];
      await nextTick();
      edges.value = currentRule.value.edges || [];
      console.log('Loaded rule from route:', currentRule.value);
    } catch (error) {
      if (error instanceof ApiError) {
        toast.add({
          severity: 'error',
          summary: 'Rule not found',
          detail: error.detail
        });
      }
      // Fall back to empty editor
      currentRule.value = null;
    }

    // Automatically run validation if in read-only mode
    if (isReadOnly.value && currentRule.value) {
      await runFlow();
    }
  }

  // Mark as loaded after initial data is synced, so the watcher doesn't
  // trigger a spurious save from the initial load.
  await nextTick();
  isLoaded.value = true;

  // Push the initial loaded state so the first undo reverts to it
  pushState();
});

onBeforeUnmount(() => {
  if (autoSaveTimeout.value) {
    clearTimeout(autoSaveTimeout.value);
  }
  if (historyDebounce.value) {
    clearTimeout(historyDebounce.value);
  }
  validationResults.value = null;
  nodeValidationStates.value.clear();
});

// Provide validation state and read-only flag for child components
provide('getNodeValidationState', getNodeValidationState);
provide('isReadOnly', isReadOnly);

</script>

<template>
  <div class="dnd-flow" @drop="onDrop">
    <VueFlow v-model:edges="edges" :nodeTypes="nodeTypes" v-model:nodes="nodes" class="relative" @dragleave="onDragLeave"
             @dragover="onDragOver"
             :class="{'read-only-flow': isReadOnly}"
             :nodesDraggable="!isReadOnly"
             :nodesConnectable="!isReadOnly"
             :elementsSelectable="true"
             :deleteKeyCode="isReadOnly ? null : ['Backspace', 'Delete']">
      <div class="absolute top-5 right-5 z-10 flex gap-3">
        <button
          v-if="!isReadOnly"
          class="bg-red-500 rounded-md px-5 py-2 text-white text-sm font-medium cursor-pointer hover:bg-red-600 disabled:opacity-50 disabled:cursor-not-allowed min-w-[100px]"
          :disabled="isSaving || isValidating"
          @click="clearFlow">
          Clear
        </button>
        <button
          v-if="!isReadOnly"
          class="bg-purple-500 rounded-md px-5 py-2 text-white text-sm font-medium cursor-pointer hover:bg-purple-600 disabled:opacity-50 disabled:cursor-not-allowed min-w-[100px]"
          :disabled="!currentRule || isSaving || isValidating"
          @click="saveFlow(true)">
          {{ isSaving ? 'Saving...' : 'Save' }}
        </button>
        <button
          class="bg-green-500 rounded-md px-5 py-2 text-white text-sm font-medium cursor-pointer hover:bg-green-600 disabled:opacity-50 disabled:cursor-not-allowed min-w-[100px]"
          :disabled="!currentRule || isValidating"
          @click="runFlow">
          {{ isValidating ? 'Validating...' : 'Validate' }}
        </button>
      </div>

      <!-- Global Confidence Score Display -->
      <div
        v-if="validationResults"
        class="absolute top-5 left-5 z-10 bg-white rounded-lg shadow-lg px-4 py-3 border-2 border-blue-500">
        <div class="text-xs font-semibold text-gray-600 uppercase tracking-wide mb-1">Confidence Score</div>
        <div class="text-2xl font-bold text-blue-600">
          {{ (validationResults.validation_result.confidence * 100).toFixed(1) }}%
        </div>
        <div class="text-xs text-gray-500">
          Score: {{ validationResults.validation_result.earned_points.toFixed(2) }} / {{ currentRule?.maxPoints?.toFixed(2) || '0.00' }}
        </div>
      </div>

      <div :style="{
          backgroundColor: isDragOver ? '#e7f3ff' : 'transparent'
        }" class="dropzone-background transition-colors duration-200 ease-in-out">
        <Background :gap="20" :size="2" pattern-color="#BDBDBD"/>
        <div class="overlay">
          <p v-if="isDragOver">Drop here</p>
        </div>
      </div>
    </VueFlow>
    <BehaviorSidebar v-if="!isReadOnly"/>
  </div>
  <Toast class="text-black" position="top-center"/>
</template>

<style scoped>
/* Disable pointer events on specific interactive elements inside read-only flow, 
   except for the node wrappers themselves so tooltips still work */
.read-only-flow :deep(.vue-flow__node input),
.read-only-flow :deep(.vue-flow__node select),
.read-only-flow :deep(.vue-flow__node textarea),
.read-only-flow :deep(.vue-flow__node button),
.read-only-flow :deep(.vue-flow__node label) {
  pointer-events: none !important;
}
</style>
