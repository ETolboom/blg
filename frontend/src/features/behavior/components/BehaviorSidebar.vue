<script lang="ts" setup>
import useDragAndDrop from '../composables/useDragAndDrop.ts'
import {NODE_TYPES} from '../types/nodeRegistry.ts'

const {onDragStart} = useDragAndDrop()

</script>

<template>
  <aside>
    <div class="description">You can drag these nodes to the pane.</div>
    <div class="node-group">
      <div class="group-title">Checks</div>
      <div class="nodes">
        <div :draggable="true" class="custom-node check-node-preview"
             @dragstart="onDragStart($event, NODE_TYPES.ELEMENT_CHECK)">
          Element Check
        </div>
        <div :draggable="true" class="custom-node check-node-preview"
             @dragstart="onDragStart($event, NODE_TYPES.GATEWAY_CHECK)">
          Gateway Check
        </div>
      </div>
    </div>
    <div class="node-group">
      <div class="group-title">Connectors</div>
      <div class="nodes">
        <div :draggable="true" class="custom-node connector-node-preview xor"
             @dragstart="onDragStart($event, NODE_TYPES.XOR)">
          XOR
        </div>
        <div :draggable="true" class="custom-node connector-node-preview and"
             @dragstart="onDragStart($event, NODE_TYPES.AND)">
          AND
        </div>
        <div :draggable="true" class="custom-node relationship-node-preview followed"
             @dragstart="onDragStart($event, NODE_TYPES.FOLLOWED_BY)">
          Followed By
        </div>
      </div>
    </div>
    <div class="node-group">
      <div class="group-title">Special Nodes</div>
      <div class="nodes">
        <div :draggable="true" class="custom-node end-node-preview"
             @dragstart="onDragStart($event, NODE_TYPES.END_NODE)">
          End Node
        </div>
        <div :draggable="true" class="custom-node notes-node-preview"
             @dragstart="onDragStart($event, NODE_TYPES.NOTES_NODE)">
          Notes
        </div>
        <div :draggable="true" class="custom-node points-node-preview"
             @dragstart="onDragStart($event, NODE_TYPES.POINTS_NODE)">
          Points
        </div>
      </div>
    </div>
  </aside>
</template>