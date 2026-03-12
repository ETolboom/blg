import type { CheckNodeData, ConnectorNodeData, EndNodeData, NoteNodeData, RelationshipConnectorData, PointsNodeData } from './nodes.ts'

export const NODE_TYPES = {
    ELEMENT_CHECK: 'elementCheck',
    GATEWAY_CHECK: 'gatewayCheck',
    XOR: 'xorConnector',
    AND: 'andConnector',
    FOLLOWED_BY: 'followedByConnector',
    END_NODE: 'endNode',
    NOTES_NODE: 'notesNode',
    POINTS_NODE: 'pointsNode',
} as const;

export type NodeType = typeof NODE_TYPES[keyof typeof NODE_TYPES]

export const NODE_CATEGORIES = {
    CHECK: [NODE_TYPES.ELEMENT_CHECK, NODE_TYPES.GATEWAY_CHECK, NODE_TYPES.POINTS_NODE],
    CONNECTOR: [NODE_TYPES.XOR, NODE_TYPES.AND, NODE_TYPES.FOLLOWED_BY],
    TERMINAL: [NODE_TYPES.END_NODE],
    ANNOTATION: [NODE_TYPES.NOTES_NODE],
} as const;

export function isValidNodeType(type: unknown): type is NodeType {
    return Object.values(NODE_TYPES).includes(type as NodeType)
}

export interface NodeMetadata<T = unknown> {
    displayName: string
    defaultData: () => T
    category: keyof typeof NODE_CATEGORIES
    allowedTargets: readonly NodeType[]
    allowedSources: readonly NodeType[]
}

export const NODE_REGISTRY = {
    [NODE_TYPES.ELEMENT_CHECK]: {
        displayName: 'Element Check',
        defaultData: (): CheckNodeData => ({
            label: 'Element Check',
            points: 0.0,
            checkType: 'element',
            elementType: 'task',
        }),
        category: 'CHECK',
        allowedTargets: [
            NODE_TYPES.XOR,
            NODE_TYPES.AND,
            NODE_TYPES.FOLLOWED_BY,
            NODE_TYPES.END_NODE,
            NODE_TYPES.POINTS_NODE,
        ],
        allowedSources: [
            NODE_TYPES.ELEMENT_CHECK,
            NODE_TYPES.GATEWAY_CHECK,
            NODE_TYPES.XOR,
            NODE_TYPES.AND,
            NODE_TYPES.FOLLOWED_BY,
        ],
    } satisfies NodeMetadata<CheckNodeData>,

    [NODE_TYPES.GATEWAY_CHECK]: {
        displayName: 'Gateway Check',
        defaultData: (): CheckNodeData => ({
            label: 'Gateway Check',
            points: 0.0,
            checkType: 'gateway',
            gatewayType: 'event',
            gatewayOutcomes: [],
            isGatewayChecked: false,
            isOutcomeChecked: false,
        }),
        category: 'CHECK',
        allowedTargets: [
            NODE_TYPES.XOR,
            NODE_TYPES.AND,
            NODE_TYPES.FOLLOWED_BY,
            NODE_TYPES.END_NODE,
            NODE_TYPES.POINTS_NODE,
        ],
        allowedSources: [
            NODE_TYPES.ELEMENT_CHECK,
            NODE_TYPES.GATEWAY_CHECK,
            NODE_TYPES.XOR,
            NODE_TYPES.AND,
            NODE_TYPES.FOLLOWED_BY,
        ],
    } satisfies NodeMetadata<CheckNodeData>,

    [NODE_TYPES.POINTS_NODE]: {
        displayName: 'Points',
        defaultData: (): PointsNodeData => ({
            label: 'Points',
            points: 0.0,
        }),
        category: 'CHECK',
        allowedTargets: [
            NODE_TYPES.XOR,
            NODE_TYPES.AND,
            NODE_TYPES.FOLLOWED_BY,
            NODE_TYPES.END_NODE,
        ],
        allowedSources: [
            NODE_TYPES.ELEMENT_CHECK,
            NODE_TYPES.GATEWAY_CHECK,
            NODE_TYPES.XOR,
            NODE_TYPES.AND,
            NODE_TYPES.FOLLOWED_BY,
        ],
    } satisfies NodeMetadata<PointsNodeData>,

    [NODE_TYPES.XOR]: {
        displayName: 'XOR',
        defaultData: (): ConnectorNodeData => ({
            label: 'XOR',
            connectorType: NODE_TYPES.XOR,
        }),
        category: 'CONNECTOR',
        allowedTargets: [
            NODE_TYPES.ELEMENT_CHECK,
            NODE_TYPES.GATEWAY_CHECK,
            NODE_TYPES.XOR,
            NODE_TYPES.AND,
            NODE_TYPES.FOLLOWED_BY,
            NODE_TYPES.END_NODE,
            NODE_TYPES.POINTS_NODE,
        ],
        allowedSources: [
            NODE_TYPES.ELEMENT_CHECK,
            NODE_TYPES.GATEWAY_CHECK,
            NODE_TYPES.XOR,
            NODE_TYPES.AND,
            NODE_TYPES.FOLLOWED_BY,
            NODE_TYPES.POINTS_NODE,
        ],
    } satisfies NodeMetadata<ConnectorNodeData>,

    [NODE_TYPES.AND]: {
        displayName: 'AND',
        defaultData: (): ConnectorNodeData => ({
            label: 'AND',
            connectorType: NODE_TYPES.AND,
        }),
        category: 'CONNECTOR',
        allowedTargets: [
            NODE_TYPES.ELEMENT_CHECK,
            NODE_TYPES.GATEWAY_CHECK,
            NODE_TYPES.XOR,
            NODE_TYPES.AND,
            NODE_TYPES.FOLLOWED_BY,
            NODE_TYPES.END_NODE,
            NODE_TYPES.POINTS_NODE,
        ],
        allowedSources: [
            NODE_TYPES.ELEMENT_CHECK,
            NODE_TYPES.GATEWAY_CHECK,
            NODE_TYPES.XOR,
            NODE_TYPES.AND,
            NODE_TYPES.FOLLOWED_BY,
            NODE_TYPES.POINTS_NODE,
        ],
    } satisfies NodeMetadata<ConnectorNodeData>,

    [NODE_TYPES.FOLLOWED_BY]: {
        displayName: 'Followed By',
        defaultData: (): RelationshipConnectorData => ({
            label: 'Followed By',
            relationshipType: 'followedBy',
            idealDistance: 1,
            maxDistance: 2,
        }),
        category: 'CONNECTOR',
        allowedTargets: [
            NODE_TYPES.ELEMENT_CHECK,
            NODE_TYPES.GATEWAY_CHECK,
            NODE_TYPES.XOR,
            NODE_TYPES.AND,
            NODE_TYPES.FOLLOWED_BY,
            NODE_TYPES.END_NODE,
            NODE_TYPES.POINTS_NODE,
        ],
        allowedSources: [
            NODE_TYPES.ELEMENT_CHECK,
            NODE_TYPES.GATEWAY_CHECK,
            NODE_TYPES.XOR,
            NODE_TYPES.AND,
            NODE_TYPES.FOLLOWED_BY,
            NODE_TYPES.POINTS_NODE,
        ],
    } satisfies NodeMetadata<RelationshipConnectorData>,

    [NODE_TYPES.END_NODE]: {
        displayName: 'End',
        defaultData: (): EndNodeData => ({
            label: 'End',
        }),
        category: 'TERMINAL',
        allowedTargets: [],
        allowedSources: [
            NODE_TYPES.ELEMENT_CHECK,
            NODE_TYPES.GATEWAY_CHECK,
            NODE_TYPES.XOR,
            NODE_TYPES.AND,
            NODE_TYPES.FOLLOWED_BY,
            NODE_TYPES.POINTS_NODE,
        ],
    } satisfies NodeMetadata<EndNodeData>,

    [NODE_TYPES.NOTES_NODE]: {
        displayName: 'Notes',
        defaultData: (): NoteNodeData => ({
            label: 'Notes',
            noteText: '',
        }),
        category: 'ANNOTATION',
        allowedTargets: [],
        allowedSources: [],
    } satisfies NodeMetadata<NoteNodeData>,
} as const satisfies Record<NodeType, NodeMetadata>;

export function isConnectionAllowed(
    sourceType: NodeType | undefined,
    targetType: NodeType | undefined
): boolean {
    if (!sourceType || !targetType) return false;
    if (!isValidNodeType(sourceType) || !isValidNodeType(targetType)) return false;

    const sourceMetadata = NODE_REGISTRY[sourceType];
    return (sourceMetadata.allowedTargets as readonly NodeType[]).includes(targetType)
}

export function getDefaultNodeData(type: NodeType): ReturnType<NodeMetadata['defaultData']> {
    const metadata = NODE_REGISTRY[type];
    return metadata.defaultData()
}

export function getNodeDisplayName(type: NodeType): string {
    return NODE_REGISTRY[type].displayName
}

export function getNodesByCategory(category: keyof typeof NODE_CATEGORIES): readonly NodeType[] {
    return NODE_CATEGORIES[category]
}
