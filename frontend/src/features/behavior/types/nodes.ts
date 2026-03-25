import type { NodeProps } from '@vue-flow/core'

export interface BaseNodeData {
    label?: string
    flagged?: boolean
}

export interface CheckNodeData extends BaseNodeData {
    label?: string
    checkType?: 'element' | 'gateway'

    // Gateway specific
    gatewayType?: 'event' | 'xor' | 'parallel'
    gatewayOutcomes?: string[]
    isGatewayChecked?: boolean
    isOutcomeChecked?: boolean

    // Element specific
    elementType?: 'task' | 'data' | 'event'
    taskType?: string
    dataType?: string
    eventType?: string
    eventPosition?: 'Start' | 'Intermediate' | 'End'
    eventBehavior?: 'Catch' | 'Boundary' | 'Throw'
    isInterrupting?: 'Interrupting' | 'Non-Interrupting'
    hasBoundaryEvent?: boolean
    boundaryEventNodeId?: string | null
    boundaryFollowedByNodeId?: string | null
    parentNodeId?: string
}

export interface ConnectorNodeData extends BaseNodeData {
    connectorType?: 'xorConnector' | 'andConnector'
}

export interface RelationshipConnectorData extends BaseNodeData {
    relationshipType?: string
    idealDistance?: number
    maxDistance?: number
}

export interface EndNodeData extends BaseNodeData {
    endNodeType?: 'end' | 'error' | 'message'
}

export interface NoteNodeData extends BaseNodeData {
    noteText?: string
}

export interface PointsNodeData extends BaseNodeData {
    points?: number
    borderColor?: string
}

export type CheckNodeProps = NodeProps<CheckNodeData>
export type ConnectorNodeProps = NodeProps<ConnectorNodeData>
export type RelationshipConnectorNodeProps = NodeProps<RelationshipConnectorData>
export type EndNodeProps = NodeProps<EndNodeData>
export type NoteNodeProps = NodeProps<NoteNodeData>
export type PointsNodeProps = NodeProps<PointsNodeData>
