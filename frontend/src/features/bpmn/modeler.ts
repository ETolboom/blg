import BpmnModeler from 'bpmn-js/lib/Modeler';
import BPMNAnalyzerModule from "@/features/bpmn/extensions/modeler";

export async function createModeler(
  container: HTMLElement,
  reference_xml: string
): Promise<BpmnModeler | undefined> {
  const modeler = new BpmnModeler({
    container: container,
    additionalModules: [
      BPMNAnalyzerModule,
    ]
  });

  try {
    const { warnings } = await modeler.importXML(reference_xml);

    modeler.get('canvas').zoom("fit-viewport");

    if (warnings.length) {
      console.warn('Diagram loaded with warnings', warnings);
    }

    return modeler;
  } catch (err) {
    console.error('Could not load diagram', err);
    return undefined;
  }
}
