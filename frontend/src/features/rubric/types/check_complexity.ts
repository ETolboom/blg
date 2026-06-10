export enum CheckComplexity {
    SIMPLE = "0",
    CONFIGURABLE = "1",
    COMPLEX = "2"
}

export const CheckComplexityLabels: Record<CheckComplexity, string> = {
    [CheckComplexity.SIMPLE]: 'Quality Checks (Model-Agnostic)',
    [CheckComplexity.CONFIGURABLE]: 'Simple (Model-Dependent)',
    [CheckComplexity.COMPLEX]: 'Complex (Model-Dependent)'
};

export type CheckComplexityType = CheckComplexity;

/** Narrow an arbitrary string to a CheckComplexity enum value. */
export function isCheckComplexity(value: string): value is CheckComplexity {
    return value in CheckComplexityLabels;
}