import type {Node, XYPosition} from '@vue-flow/core';
import {useVueFlow} from '@vue-flow/core';
import {ref, type Ref, watch} from 'vue';
import {getDefaultNodeData, type NodeType} from '../types/nodeRegistry.ts';

let id = 0;
const getId = (existingNodes: Node[]): string => {
    // Find the highest existing dndnode ID to avoid collisions
    const maxId = existingNodes.reduce((max, node) => {
        const match = node.id.match(/^dndnode_(\d+)$/);
        if (match) {
            const nodeNum = parseInt(match[1], 10);
            return Math.max(max, nodeNum);
        }
        return max;
    }, -1);

    // Start from max + 1 if there are existing nodes
    if (maxId >= id) {
        id = maxId + 1;
    }

    return `dndnode_${id++}`;
};

const state = {
    draggedType: ref<NodeType | null>(null),
    isDragOver: ref<boolean>(false),
    isDragging: ref<boolean>(false),
};

interface UseDragAndDropReturn {
    draggedType: Ref<NodeType | null>
    isDragOver: Ref<boolean>
    isDragging: Ref<boolean>
    onDragStart: (event: DragEvent, type: NodeType) => void
    onDragLeave: () => void
    onDragOver: (event: DragEvent) => void
    onDrop: (event: DragEvent) => void
}

export default function useDragAndDrop(): UseDragAndDropReturn {
    const {draggedType, isDragOver, isDragging} = state;

    const {addNodes, screenToFlowCoordinate, onNodesInitialized, updateNode, getNodes} = useVueFlow();

    watch(isDragging, (dragging: boolean) => {
        document.body.style.userSelect = dragging ? 'none' : ''
    });

    function onDragStart(event: DragEvent, type: NodeType): void {
        if (event.dataTransfer) {
            event.dataTransfer.setData('application/vueflow', type);
            event.dataTransfer.effectAllowed = 'move'
        }

        draggedType.value = type;
        isDragging.value = true;

        document.addEventListener('drop', onDragEnd)
    }

    function onDragOver(event: DragEvent): void {
        event.preventDefault();

        if (draggedType.value) {
            isDragOver.value = true;

            if (event.dataTransfer) {
                event.dataTransfer.dropEffect = 'move'
            }
        }
    }

    function onDragLeave(): void {
        isDragOver.value = false
    }

    function onDragEnd(): void {
        isDragging.value = false;
        isDragOver.value = false;
        draggedType.value = null;
        document.removeEventListener('drop', onDragEnd)
    }

    function onDrop(event: DragEvent): void {
        const position: XYPosition = screenToFlowCoordinate({
            x: event.clientX,
            y: event.clientY,
        });

        const existingNodes = getNodes.value;
        const nodeId = getId(existingNodes);
        const type = draggedType.value;

        if (!type) return;

        const nodeData = getDefaultNodeData(type);

        const newNode: Node = {
            id: nodeId,
            type: type,
            position,
            data: nodeData,
        };

        const {off} = onNodesInitialized(() => {
            updateNode(nodeId, (node) => ({
                position: {
                    x: node.position.x - (node.dimensions?.width ?? 0) / 2,
                    y: node.position.y - (node.dimensions?.height ?? 0) / 2
                },
            }));

            off()
        });

        addNodes(newNode)
    }

    return {
        draggedType,
        isDragOver,
        isDragging,
        onDragStart,
        onDragLeave,
        onDragOver,
        onDrop,
    }
}
