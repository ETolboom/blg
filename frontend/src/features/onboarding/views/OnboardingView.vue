<script lang="ts" setup>
import {ref, watch} from "vue";
import Stepper from 'primevue/stepper';
import StepList from 'primevue/steplist';
import StepPanels from 'primevue/steppanels';
import Column from 'primevue/column';
import TreeTable from 'primevue/treetable';
import Button from "primevue/button";
import Step from 'primevue/step';
import StepPanel from 'primevue/steppanel';
import {checkService, type AnalysisNode, rubricService} from "@/services";
import { CheckComplexityLabels, isCheckComplexity } from "@/features/rubric/types/check_complexity";

const emit = defineEmits<{
  onboarded: []
}>();

const pdfFileInput = ref<HTMLInputElement>();
const pdfFileName = ref<string>();

const fileInput = ref<HTMLInputElement>();
const fileName = ref<string>();
const selectedChecks = ref<string[]>([]);
const selectedKeys = ref<Record<string, { checked: boolean; partialChecked: boolean }>>();
const isBusy = ref<boolean>(false);
const nodes = ref<AnalysisNode[] | null>(null);
const loadingText = ref<string>("Analyzing.");

const handleFileChange = (): void => {
  if (!fileInput.value?.files?.[0]) return;
  fileName.value = fileInput.value.files[0].name;
};

const handlePdfFileChange = (): void => {
  if (!pdfFileInput.value?.files?.[0]) return;
  pdfFileName.value = pdfFileInput.value.files[0].name;
};

const analyzeFile = async (): Promise<void> => {
  if (nodes.value && nodes.value.length > 0) {
    nodes.value = null;
    selectedChecks.value = [];
    selectedKeys.value = undefined;
  }

  if (!fileName.value || fileName.value === "") {
    alert("Please select a file!");
    return;
  }

  if (!fileInput.value?.files?.[0]) {
    alert("No file selected!");
    return;
  }

  isBusy.value = true;

  let dots = 1;
  const interval = setInterval(() => {
    dots = (dots % 3) + 1;
    loadingText.value = "Analyzing" + ".".repeat(dots);
  }, 500);

  try {
    const rawNodes = await checkService.analyzeFile(fileInput.value.files[0]);
    nodes.value = rawNodes.map(node => {
      // Category nodes carry a CheckComplexity value as their name; relabel them.
      if (isCheckComplexity(node.data.name)) {
        return {
          ...node,
          data: {
            ...node.data,
            name: CheckComplexityLabels[node.data.name]
          }
        };
      }
      return node;
    });
  } catch (error) {
    console.error(error);
  } finally {
    isBusy.value = false;
    clearInterval(interval);
  }
};

watch(selectedKeys, (keys) => {
  if (!keys) {
    selectedChecks.value = [];
    return;
  }

  // Filter for leaf nodes (keys containing "-") that are fully checked
  selectedChecks.value = Object.entries(keys)
      .filter(([key, value]) => key.includes("-") && value.checked)
      .map(([key]) => key);
}, { deep: true });

const finalizeOnboarding = async (): Promise<void> => {
  isBusy.value = true;

  const check_ids = selectedChecks.value
      .map(key => {
        const node = findNodeById(nodes.value, key);
        return node ? node.data.id : null;
      })
      .filter((id): id is string => id !== null);

  let reference_xml = "";
  const file = fileInput.value?.files?.[0];

  if (file) {
    reference_xml = await readFileAsText(file);
  }

  try {
    await rubricService.createRubric({
      assignment: {
        id: crypto.randomUUID(),
        reference_xml: reference_xml,
      },
      checks: check_ids,
    });

    // Upload supplement PDF if selected
    const pdfFile = pdfFileInput.value?.files?.[0];
    if (pdfFile) {
      await rubricService.uploadSupplement(pdfFile);
    }

    emit('onboarded');
  } catch (error) {
    console.error(error);
  } finally {
    isBusy.value = false;
  }
};

const readFileAsText = (file: File): Promise<string> => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = (e) => resolve(e.target?.result as string);
    reader.onerror = (e) => reject(e);
    reader.readAsText(file);
  });
};

const findNodeById = (nodes: AnalysisNode[] | null, targetKey: string): AnalysisNode | null => {
  if (!nodes) return null;

  const search = (nodeArray: AnalysisNode[]): AnalysisNode | null => {
    for (const node of nodeArray) {
      if (node.key === targetKey) {
        return node;
      }

      if (node.children && node.children.length > 0) {
        const result = search(node.children);
        if (result) return result;
      }
    }
    return null;
  };

  return search(nodes);
};

</script>

<template>
  <div class="card flex w-10/12 lg:w-1/2 h-full pt-8">
    <Stepper class="basis-[50rem]" value="1">
      <StepList>
        <Step value="1">Welcome</Step>
        <Step value="2">Assignment</Step>
        <Step value="3">Checks</Step>
      </StepList>
      <StepPanels class="h-full">
        <StepPanel v-slot="{ activateCallback }" value="1">
          <div class="flex flex-col h-48">
            <div
                class="border-2 border-gray-200 rounded bg-gray-100 p-4 flex-auto flex flex-col justify-start font-medium">
              <h1 class="text-xl pb-2 font-bold">Welcome to BLG!</h1>
              <div class="font-medium flex flex-col gap-y-1">
                <span>BPMN Learn & Grade (BLG) is designed to help you effectively grade student BPMN submissions!</span>
                <span>In order to get started a small onboarding process will first take place.</span>
                <span>Click "Next" in the bottom right corner of this dialog to get started.</span>
              </div>
            </div>
          </div>
          <div class="flex pt-6 justify-end">
            <Button icon="pi pi-arrow-right" iconPos="right" label="Next" @click="activateCallback('2')"/>
          </div>
        </StepPanel>
        <StepPanel v-slot="{ activateCallback }" class="h-full" value="2">
          <div class="flex flex-col">
            <div
                class="border-2 border-gray-200 rounded bg-gray-100 p-4 flex-auto flex flex-col justify-start font-medium">
              <h1 class="text-xl pb-2 font-bold">Assignment description</h1>
              <div class="font-medium flex flex-col gap-y-1">
                <span>When grading its useful to keep a reference to the assignment description available at all times.</span>
                <span>You can upload a PDF file containing the assignment description below.</span>
              </div>
            </div>
            
            <div class="mt-4 px-4 py-2 border-2 border-gray-200 rounded bg-gray-100 w-full justify-start">
                <div class="w-full flex flex-row justify-between">
                    <div class="custom-file-upload">
                        <input
                            id="pdf-upload"
                            ref="pdfFileInput"
                            class="hidden"
                            type="file"
                            accept=".pdf"
                            @change="handlePdfFileChange"
                        />
                        <Button :disabled="isBusy" icon="pi pi-upload" label="Select PDF"
                                @click="pdfFileInput?.click()"></Button>
                        <span class="pl-2 font-medium truncate">{{ pdfFileName ?? "No file selected" }}</span>
                    </div>
                </div>
            </div>
            
            <div class="flex pt-6 justify-between">
              <Button icon="pi pi-arrow-left" label="Back" severity="secondary" @click="activateCallback('1')"/>
              <Button icon="pi pi-arrow-right" iconPos="right" label="Next" @click="activateCallback('3')"/>
            </div>
          </div>
        </StepPanel>
        <StepPanel v-slot="{ activateCallback }" value="3">
          <div class="flex flex-col">
            <div
                class="border-2 border-gray-200 rounded bg-gray-100 p-4 flex-auto flex flex-col justify-start font-medium">
              <h1 class="text-xl pb-2 font-bold">Checks</h1>
              <div class="font-medium flex flex-col gap-y-1">
                <span>One of the selling points of BLG is of course the checks that can be used to grade.</span>
                <span>If you have an existing BPMN file, you can drop it in the space below</span>
              </div>
            </div>
            <!-- Step 1. Uploading BPMN file-->
            <div class="mt-4 px-4 py-2 border-2 border-gray-200 rounded bg-gray-100 w-full justify-start">
              <h1 class="text-xl pb-4 font-bold">1. Select a BPMN file</h1>
              <div class="w-full flex flex-row justify-between">
                <div class="custom-file-upload">
                  <input
                      id="file-upload"
                      ref="fileInput"
                      class="hidden"
                      type="file"
                      @change="handleFileChange"
                  />
                  <Button :disabled="isBusy" icon="pi pi-upload" label="Select file"
                          @click="fileInput?.click()"></Button>
                  <span class="pl-2 font-medium truncate">{{ fileName ?? "No file selected" }}</span>
                </div>
                <Button
                    :disabled="!fileName || isBusy"
                    icon="pi pi-check"
                    label="Analyze"
                    @click="analyzeFile"
                />
              </div>
            </div>
            <!-- Step 2. Selecting checks -->
            <div class="mt-4 px-4 py-2 border-2 border-gray-200 rounded bg-gray-100 w-full justify-start">
              <h1 class="text-xl pb-4 font-bold">2. Select checks</h1>
              <div class="font-medium flex flex-col gap-y-1">
                <span>Below you will find a list of checks that are applicable to your model.</span>
                <span>Please confirm the initial selection of checks that you may want to add.</span>
              </div>
            </div>
            <template v-if="nodes">
              <TreeTable v-model:selectionKeys="selectedKeys" :value="nodes"
                         class="border-2 border-gray-200 rounded bg-gray-100 mt-2"
                         selectionMode="checkbox">
                <Column expander field="name" header="Name" style="width: 34%"></Column>
                <Column field="description" header="Description" style="width: 66%"></Column>
              </TreeTable>
            </template>
            <template v-else-if="isBusy">
              <div class="border-2 border-gray-200 rounded bg-gray-100 mt-2 flex justify-center items-center">
                <span class="font-medium font-mono text-md p-4">{{
                    loadingText
                  }}</span>
              </div>
            </template>
            <template v-else>
              <div class="border-2 border-gray-200 rounded bg-gray-100 mt-2 flex justify-center items-center">
                <span class="font-medium font-mono text-md p-4">Awaiting analysis...</span>
              </div>
            </template>
            <div class="mt-4 px-4 py-2 border-2 border-gray-200 rounded bg-gray-100 w-full justify-start">
              <h1 class="text-xl pb-4 font-bold">3. Confirmation</h1>
              <div class="font-medium flex flex-col gap-y-1">
                <span>Based on your selection BLG will be initialized.</span>
                <span>Any checks can be added or removed later at any point.</span>
                <span>To continue and start using BLG press the "Finalize" button.</span>
              </div>
            </div>
            <div class="flex pt-6 justify-between">
              <Button :disabled="isBusy" icon="pi pi-arrow-left" label="Back" severity="secondary"
                      @click="activateCallback('1')"/>
              <Button :disabled="!(selectedChecks.length > 0) || isBusy"
                      icon="pi pi-arrow-right" iconPos="right"
                      label="Finalize"
                      @click="finalizeOnboarding"/>
            </div>
          </div>
        </StepPanel>
      </StepPanels>
    </Stepper>
  </div>
</template>

<style scoped>

</style>