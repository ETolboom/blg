declare module 'bpmn-js/lib/Modeler' {
    import {ModdleElement} from 'bpmn-js/lib/model/Types';

    export interface Canvas {
        zoom(scale: number | 'fit-viewport', point?: { x: number; y: number }): number;

        viewbox(box?: { x: number; y: number; width: number; height: number }): {
            x: number;
            y: number;
            width: number;
            height: number;
            scale: number;
            inner: { width: number; height: number; x: number; y: number };
            outer: { width: number; height: number };
        };

        scroll(delta: { dx: number; dy: number }): void;

        getRootElement(): ModdleElement;

        getContainer(): HTMLElement;

        resized(): void;
    }

    export interface ZoomScroll {
        toggle(newEnabled?: boolean): void;

        reset(): void;

        stepZoom(direction: 1 | -1): void;
    }

    export interface EventBus {
        on(event: string | string[], priority: number, callback: Function, that?: any): void;

        on(event: string | string[], callback: Function, that?: any): void;

        once(event: string | string[], priority: number, callback: Function, that?: any): void;

        once(event: string | string[], callback: Function, that?: any): void;

        off(event: string | string[], callback?: Function): void;

        fire(event: string, ...args: any[]): any;
    }

    export interface ElementRegistry {
        get(id: string): ModdleElement | undefined;

        getAll(): ModdleElement[];

        forEach(callback: (element: ModdleElement) => void): void;

        filter(callback: (element: ModdleElement) => boolean): ModdleElement[];
    }

    export interface Modeling {
        updateProperties(element: ModdleElement, properties: Record<string, any>): void;

        setColor(elements: ModdleElement | ModdleElement[], colors: { stroke?: string; fill?: string }): void;

        removeElements(elements: ModdleElement[]): void;
    }

    export interface ModelerServices {
        canvas: Canvas;
        zoomScroll: ZoomScroll;
        eventBus: EventBus;
        elementRegistry: ElementRegistry;
        modeling: Modeling;

        [key: string]: any;
    }

    export interface ImportXMLResult {
        warnings: Array<{ message: string; error?: Error }>;
    }

    export interface SaveXMLOptions {
        format?: boolean;
        preamble?: boolean;
    }

    export interface SaveXMLResult {
        xml: string;
    }

    export default class BpmnModeler {
        constructor(options?: {
            container?: string | HTMLElement;
            width?: number | string;
            height?: number | string;
            moddleExtensions?: Record<string, any>;
            modules?: any[];
            additionalModules?: any[];
            [key: string]: any;
        });

        get<K extends keyof ModelerServices>(serviceName: K): ModelerServices[K];
        get(serviceName: string): any;

        importXML(xml: string): Promise<ImportXMLResult>;

        saveXML(options?: SaveXMLOptions): Promise<SaveXMLResult>;

        saveSVG(options?: { format?: boolean }): Promise<{ svg: string }>;

        destroy(): void;

        clear(): void;

        attachTo(parentNode: HTMLElement): void;

        detach(): void;

        on(event: string, priority: number, callback: Function, that?: any): void;
        on(event: string, callback: Function, that?: any): void;

        off(event: string, callback?: Function): void;
    }
}

declare module 'bpmn-js/lib/model/Types' {
    export interface ModdleElement {
        id: string;
        type: string;
        businessObject: any;
        parent?: ModdleElement;
        labels?: ModdleElement[];
        waypoints?: Array<{ x: number; y: number }>;
        x?: number;
        y?: number;
        width?: number;
        height?: number;

        [key: string]: any;
    }
}
