import {nextTick, ref, toRaw, type Ref} from 'vue'
import type {Edge, Node} from '@vue-flow/core'

interface HistorySnapshot {
  nodes: Node[]
  edges: Edge[]
}

const MAX_HISTORY = 50

/**
 * Strips VueFlow internal/computed properties from nodes so that
 * snapshots contain only the serializable data we control.
 */
function cloneNode(node: Node): Node {
  const raw = toRaw(node)
  return {
    id: raw.id,
    type: raw.type,
    position: {...raw.position},
    data: JSON.parse(JSON.stringify(raw.data)),
    ...(raw.parentNode ? {parentNode: raw.parentNode} : {}),
  }
}

function cloneEdge(edge: Edge): Edge {
  const raw = toRaw(edge)
  return {
    id: raw.id,
    source: raw.source,
    target: raw.target,
    ...(raw.sourceHandle ? {sourceHandle: raw.sourceHandle} : {}),
    ...(raw.targetHandle ? {targetHandle: raw.targetHandle} : {}),
  }
}

function snapshot(nodes: Node[], edges: Edge[]): HistorySnapshot {
  return {
    nodes: nodes.map(cloneNode),
    edges: edges.map(cloneEdge),
  }
}

export function useFlowHistory(
  nodesRef: Ref<Node[]>,
  edgesRef: Ref<Edge[]>,
) {
  const undoStack = ref<HistorySnapshot[]>([])
  const redoStack = ref<HistorySnapshot[]>([])
  // Flag to suppress the change-watcher while we're restoring a snapshot
  const isRestoring = ref(false)

  const canUndo = () => undoStack.value.length > 0
  const canRedo = () => redoStack.value.length > 0

  /** Push the current state onto the undo stack (call before a change is applied, or on a debounce). */
  function pushState() {
    if (isRestoring.value) return
    undoStack.value.push(snapshot(nodesRef.value, edgesRef.value))
    if (undoStack.value.length > MAX_HISTORY) {
      undoStack.value.shift()
    }
    // Any new change invalidates the redo stack
    redoStack.value = []
  }

  function applySnapshot(snap: HistorySnapshot) {
    isRestoring.value = true
    nodesRef.value = snap.nodes
    edgesRef.value = snap.edges
    // Reset once Vue Flow has synced. nextTick is render-ordered, unlike a
    // 0ms setTimeout which only guesses at the sync timing.
    void nextTick(() => {
      isRestoring.value = false
    })
  }

  function undo() {
    if (!canUndo()) return
    // Save current state to redo stack before restoring
    redoStack.value.push(snapshot(nodesRef.value, edgesRef.value))
    const prev = undoStack.value.pop()!
    applySnapshot(prev)
  }

  function redo() {
    if (!canRedo()) return
    // Save current state to undo stack before restoring
    undoStack.value.push(snapshot(nodesRef.value, edgesRef.value))
    const next = redoStack.value.pop()!
    applySnapshot(next)
  }

  return {isRestoring, canUndo, canRedo, pushState, undo, redo}
}