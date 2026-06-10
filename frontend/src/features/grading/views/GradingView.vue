<script lang="ts" setup>
import {onMounted, onUnmounted, ref, shallowRef, useTemplateRef, nextTick} from "vue";
import {useRouter} from "vue-router";
import {ProgressBar, useToast, Tabs, TabList, Tab, TabPanels, TabPanel} from "primevue";
import {createModeler} from "@/features/bpmn/modeler";
import BpmnModeler from "bpmn-js/lib/Modeler";
import {checkService, ApiError, projectService, rubricService, submissionService, toastError, toastSuccess, REFERENCE_FILENAME} from "@/services";
import type {Rubric, Rubric as RubricType} from "@/features/rubric/types/rubric";
import GradingZoomControls from "@/features/grading/components/GradingZoomControls.vue";
import GradingHeader from "@/features/grading/components/GradingHeader.vue";
import ReferenceHeader from "@/features/grading/components/ReferenceHeader.vue";
import OnboardingView from "@/features/onboarding/views/OnboardingView.vue";
import RubricLayout from "@/features/rubric/layouts/RubricLayout.vue";

const toast = useToast();
const router = useRouter();

const bpmn = useTemplateRef<HTMLDivElement>("bpmn-container");
const modeler = shallowRef<BpmnModeler>();
const rubric = ref<RubricType>();
const submission_name = ref<string>();
const reference_xml = ref<string>();
const submission_xml = ref<string>();
const shouldOnboard = ref(false);
const isLoading = ref(true);
const isModelerReady = ref(false);
const isSavingReference = ref(false);
const isRegradingAfterSave = ref(false);
const hasReferenceChanges = ref(false);

const loadRubric = async () => {
  try {
    const fetchedRubric = await rubricService.getRubric();
    
    // If we already have a rubric, just update the criteria to keep current state if possible,
    // but ideally we want the latest definition.
    if (rubric.value) {
      rubric.value.criteria = fetchedRubric.criteria;
      // We might want to update other fields if they changed, e.g. custom scores calculated backend side?
      // For now, syncing criteria is key.
      rubric.value.assignment = fetchedRubric.assignment; 
    } else {
      rubric.value = fetchedRubric;
    }
    
    reference_xml.value = rubric.value.assignment.reference_xml;
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) {
      isLoading.value = false;
      shouldOnboard.value = true;
    } else {
      toastError(toast, 'Could not load rubric', error);
    }
  }
};

// Named so it can be removed in onUnmounted (an anonymous closure could never be).
const handleResize = () => {
  modeler.value?.get('canvas').resized();
};

// Single place that creates the modeler and wires its listeners, shared by the
// initial mount and the post-onboarding path so the setup never drifts or
// double-registers. Returns false (after toasting) if it couldn't initialize.
const initModeler = async (): Promise<boolean> => {
  if (!bpmn.value || !reference_xml.value) {
    toast.add({
      severity: 'error',
      summary: 'Initialization failed',
      detail: 'Container or reference XML not available'
    });
    return false;
  }

  modeler.value = await createModeler(bpmn.value, reference_xml.value);

  if (!modeler.value) {
    toast.add({severity: 'error', summary: 'Initialization failed', detail: 'Could not create modeler'});
    return false;
  }

  modeler.value.get('eventBus').on('commandStack.changed', () => {
    if (activeTab.value === '1') hasReferenceChanges.value = true;
  });

  // Idempotent: removing an unregistered handler is a no-op, so re-initializing
  // (e.g. after onboarding) never stacks duplicate resize listeners.
  window.removeEventListener("resize", handleResize);
  window.addEventListener("resize", handleResize);

  isLoading.value = false;
  isModelerReady.value = true;
  return true;
};

onMounted(async () => {
  // 0. Ensure a project is active; otherwise return to the landing screen.
  // 1. Check the backend for existing rubric
  // Yes -> Load rubric
  // No -> Start onboarding
  // 2. Once rubric is loaded, create a modeler

  try {
    const { active_project } = await projectService.getActiveProject();
    if (!active_project) {
      await router.push("/");
      return;
    }
  } catch {
    await router.push("/");
    return;
  }

  await loadRubric();

  if (shouldOnboard.value) return;

  await initModeler();
});

onUnmounted(() => {
  window.removeEventListener("resize", handleResize);
  modeler.value?.destroy();
});


const updateRubric = (newRubric: Rubric) => {
  if (!rubric.value) return;

  isLoading.value = true;
  rubric.value.criteria = newRubric.criteria;
  isLoading.value = false;
};

const toggleReference = async () => {
  if (!modeler.value) return;

  isLoading.value = true;

  try {
    if (activeTab.value === '0') {
      if (submission_xml.value) {
        await modeler.value.importXML(submission_xml.value);
      }
    } else if (activeTab.value === '1') {
      if (reference_xml.value) {
        await modeler.value.importXML(reference_xml.value);
        hasReferenceChanges.value = false;
      }
    }
    
    // Supplement tab logic is handled by standard html rendering, not bpmn imports

    modeler.value.get('zoomScroll').reset();
    modeler.value.get('canvas').zoom("fit-viewport");
  } catch (err) {
    toastError(toast, 'Loading failed', err);
  }

  isLoading.value = false;
};

const activeTab = ref('1');

const onTabChange = async (event: any) => {
  activeTab.value = event;
  await nextTick();
  // Only swap the reference model when going to the Reference tab;
  // the Submission load is handled by GradingHeader via its isActive prop watcher.
  if (activeTab.value === '1') {
     await Promise.all([toggleReference(), loadRubric()]);
  }
};


const gradeSubmission = async (filename: string, model_xml: string) => {
  if (!rubric.value) return;

  isLoading.value = true;
  submission_name.value = filename;
  submission_xml.value = model_xml;

  try {
    const result = await checkService.gradeSubmission(filename);
    rubric.value.criteria = result.criteria;
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) {
      isLoading.value = false;
      shouldOnboard.value = true;
    } else {
      toastError(toast, 'Could not grade submission', error);
    }
  }

  isLoading.value = false;
};

const saveSubmission = async () => {
  if (!submission_name.value || submission_name.value === REFERENCE_FILENAME || !rubric.value) {
    return;
  }

  try {
    await submissionService.saveSubmission(submission_name.value, rubric.value.criteria);
  } catch (error) {
    toastError(toast, 'Could not save submission', error);
  }
};

const saveReference = async () => {
  if (!modeler.value) return;
  isSavingReference.value = true;
  try {
    const { xml } = await modeler.value.saveXML({ format: true });
    if (!xml) throw new Error('Could not export XML from modeler');
    const result = await rubricService.updateReference(xml);
    reference_xml.value = xml;
    hasReferenceChanges.value = false;
    toastSuccess(toast, 'Reference saved', result);

    if (submission_name.value && rubric.value) {
      isSavingReference.value = false;
      isRegradingAfterSave.value = true;
      toast.add({ severity: 'info', summary: 'Re-grading submission…', life: 2000 });
      try {
        const result = await checkService.gradeSubmission(submission_name.value);
        rubric.value.criteria = result.criteria;
        toast.add({ severity: 'success', summary: 'Submission re-graded', life: 3000 });
      } catch (error) {
        toastError(toast, 'Could not re-grade submission', error, { severity: 'warn' });
      } finally {
        isRegradingAfterSave.value = false;
      }
    } else {
      toast.add({ severity: 'info', summary: 'No submission loaded', detail: 'Open a submission to re-grade it against the updated reference', life: 4000 });
    }
  } catch (error) {
    toastError(toast, 'Could not save reference', error);
  } finally {
    isSavingReference.value = false;
  }
};

const clearReference = async () => {
  if (!modeler.value || !reference_xml.value) return;
  try {
    await modeler.value.importXML(reference_xml.value);
    modeler.value.get('canvas').zoom('fit-viewport');
    hasReferenceChanges.value = false;
  } catch (error) {
    toastError(toast, 'Could not clear changes', error);
  }
};

const onOnboarded = async () => {
  shouldOnboard.value = false;
  isLoading.value = true;

  await loadRubric();

  if (shouldOnboard.value) return;

  // Wait for the modeler container to render now that onboarding is dismissed.
  await nextTick();

  await initModeler();
};

</script>

<template>
  <template v-if="shouldOnboard">
    <div class="h-full w-full flex justify-center items-center">
      <OnboardingView @onboarded="onOnboarded"/>
    </div>
  </template>
  <template v-else>
    <!-- Loading screen -->
    <template v-if="isLoading && !isModelerReady">
      <div class="absolute bg-white top-0 z-10 h-full w-full flex flex-col justify-center items-center">
        <span class="font-mono p-2 text-2xl">Loading app...</span>
        <ProgressBar mode="indeterminate" style="height: 0.5rem; width: 16rem;"></ProgressBar>
      </div>
    </template>

    <!-- Main content -->
    <div class="flex flex-row h-full justify-between relative overflow-hidden">
      <div v-if="isLoading && isModelerReady"
           class="absolute inset-0 bg-white/80 backdrop-blur-sm z-50 flex flex-col justify-center items-center">
        <span class="font-mono p-2 text-2xl">Loading...</span>
        <ProgressBar mode="indeterminate" style="height: 0.5rem; width: 16rem;"></ProgressBar>
      </div>

      <div class="flex flex-col w-full h-full relative overflow-hidden">
        <Tabs v-model:value="activeTab" class="flex flex-col h-full w-full" @update:value="onTabChange">
          <div class="flex justify-center border-b border-gray-200 bg-gray-50/50 pt-2 shrink-0">
            <TabList>
              <Tab value="0">Submission</Tab>
              <Tab value="1">Reference</Tab>
              <Tab value="2">Supplement</Tab>
            </TabList>
          </div>
          <TabPanels class="flex-1 p-0 relative overflow-hidden">
            <!-- Render the modeler only on Submission and Reference tabs -->
            <div v-show="activeTab === '0' || activeTab === '1'" class="absolute inset-0 flex flex-col">
                <div v-show="activeTab === '0' && isModelerReady && modeler">
                  <GradingHeader :modeler="modeler!" :is-active="activeTab === '0'" @regrade="gradeSubmission" @loading="(loading) => isLoading = loading"/>
                </div>
                <ReferenceHeader v-show="activeTab === '1' && isModelerReady && modeler"
                                :has-changes="hasReferenceChanges"
                                :is-saving="isSavingReference"
                                :is-regrading="isRegradingAfterSave"
                                @save="saveReference"
                                @clear="clearReference"/>
                <div ref="bpmn-container" class="flex-1 w-full relative" :class="{'read-only-modeler': activeTab !== '1'}"/>
                <GradingZoomControls v-if="isModelerReady && modeler" :modeler="modeler"/>
            </div>

            <!-- Empty TabPanels to keep PrimeVue Tabs happy, but absolute positioning handles actual layout -->
            <TabPanel value="0" class="h-0 p-0 m-0"></TabPanel>
            <TabPanel value="1" class="h-0 p-0 m-0"></TabPanel>

            <!-- Supplement PDF Viewer -->
            <TabPanel value="2" class="h-full w-full p-0 flex flex-col">
              <div class="flex-1 w-full h-full p-4 overflow-hidden">
                <iframe
                    src="/api/rubric/supplement"
                    title="Assignment Supplement"
                    class="w-full h-full border rounded-lg shadow-sm bg-white"
                />
              </div>
            </TabPanel>
          </TabPanels>
        </Tabs>
      </div>
      <RubricLayout v-if="isModelerReady && typeof modeler !== 'undefined' && rubric"
                    :criteria="rubric.criteria"
                    :modeler="modeler!"
                    :is-editable="activeTab !== '0'"
                    :submission-name="activeTab === '0' ? submission_name : undefined"
                    @saveSubmission="saveSubmission"
                    @updateRubric="updateRubric"/>
    </div>
  </template>
  <Toast class="text-black" position="top-center"/>
</template>

<style>
.p-tablist-tab-list {
    background: transparent !important;
    border: none !important;
}

.p-tabpanels {
    padding: 0 !important;
    height: 100%;
}

.read-only-modeler .djs-palette,
.read-only-modeler .djs-context-pad,
.read-only-modeler .bjs-powered-by {
    display: none !important;
}

.read-only-modeler .djs-element {
    pointer-events: none !important;
}

.read-only-modeler .djs-direct-editing-parent {
    display: none !important;
}
</style>