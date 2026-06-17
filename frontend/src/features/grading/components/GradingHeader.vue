<script lang="ts" setup>
import {ArrowLeft, ArrowRight, PlusIcon, FileDown} from "lucide-vue-next";
import {Dialog, FileUpload, Select, useToast} from "primevue";
import type {FileUploadUploaderEvent} from "primevue/fileupload";
import {onMounted, ref, watch} from "vue";
import {submissionService, toastError} from "@/services";
import type BpmnModeler from "bpmn-js/lib/Modeler";
import type Submission from "@/features/grading/types/submission";
import GradingButton from "@/features/grading/components/GradingButton.vue";
import ExportDialog from "@/features/grading/components/ExportDialog.vue";

const props = defineProps<{
  modeler: BpmnModeler;
  isActive?: boolean;
}>();

const emit = defineEmits<{
  (e: 'regrade', filename: string, model_xml: string): void
  (e: 'loading', isLoading: boolean): void
}>();

const toast = useToast();

const uploadDialogVisible = ref<boolean>(false);
const exportDialogVisible = ref<boolean>(false);
const uploading = ref<boolean>(false);
const submissions = ref<Submission[]>([]);
const selectedSubmission = ref<Submission | null>(null);

onMounted(async () => {
  try {
    const data = await submissionService.getSubmissions();
    submissions.value = data;
    if (submissions.value.length > 0) {
      selectedSubmission.value = submissions.value[0] as Submission;
    }
  } catch (error) {
    console.error(error);
    toastError(toast, 'Loading failed', error, { fallback: 'Could not load list of submissions.' });
  }

  // Register the watcher AFTER the initial assignment so it doesn't fire for it.
  // If registered at the top level, Vue queues a watcher call for the initial
  // `selectedSubmission = submissions[0]` assignment and fires it on the next tick
  // (after isMounted would already be true), so a flag-based guard doesn't work.
  watch(selectedSubmission, async (newValue) => {
    if (!newValue) {
      props.modeler.clear();
      return;
    }
    emit('loading', true);
    try {
      const modelXml = await loadSubmission(newValue.filename);
      props.modeler.get('zoomScroll').reset();
      props.modeler.get('canvas').zoom("fit-viewport");
      emit('regrade', newValue.filename, modelXml);
    } catch (error) {
      console.error('Failed to load submission:', error);
      emit('loading', false);
    }
  });
});

// When the Submission tab becomes active, load the currently selected submission.
// This fires when the user first clicks the Submission tab after loading on Reference.
watch(() => props.isActive, async (isActive) => {
  if (isActive && selectedSubmission.value) {
    emit('loading', true);
    try {
      const modelXml = await loadSubmission(selectedSubmission.value.filename);
      props.modeler.get('zoomScroll').reset();
      props.modeler.get('canvas').zoom("fit-viewport");
      emit('regrade', selectedSubmission.value.filename, modelXml);
    } catch (error) {
      console.error('Failed to load submission on tab switch:', error);
      emit('loading', false);
    }
  }
});

const loadSubmission = async (submission: string) => {
  try {
    const diagramXML = await submissionService.getSubmission(submission);
    await props.modeler.importXML(diagramXML).catch((err: Error) => {
      toast.add({severity: 'error', summary: 'Loading failed', detail: err.message});
    });
    return diagramXML;
  } catch (error) {
    toastError(toast, 'Loading failed', error, { fallback: 'Could not load submission.' });
    throw error;
  }
};

const findSubmissionIndex = () => {
  if (!selectedSubmission.value) return -1;
  return submissions.value.findIndex(
      (item) => item.filename === selectedSubmission.value!.filename
  );
};

const previousSubmission = () => {
  const index = findSubmissionIndex();
  if (index <= 0) return;

  const newSubmission = submissions.value[index - 1];
  if (newSubmission) selectedSubmission.value = newSubmission;
};

const nextSubmission = () => {
  const index = findSubmissionIndex();
  if (index === -1) return;
  if (index === submissions.value.length - 1) return;

  const newSubmission = submissions.value[index + 1];
  if (newSubmission) selectedSubmission.value = newSubmission;
};

const openUploadDialog = () => {
  uploadDialogVisible.value = true;
};

const handleUpload = async (event: FileUploadUploaderEvent) => {
  const files = Array.isArray(event.files) ? event.files : [event.files];
  if (files.length === 0) return;

  uploading.value = true;
  try {
    const uploaded = await submissionService.uploadSubmissions(files as File[]);
    submissions.value.push(...uploaded);
    toast.add({
      severity: 'success',
      summary: 'Upload successful',
      detail: `Uploaded ${uploaded.length} submission(s).`,
      life: 3000,
    });
    uploadDialogVisible.value = false;
  } catch (error) {
    console.error(error);
    toastError(toast, 'Upload failed', error, { fallback: 'Could not upload submissions.' });
  } finally {
    uploading.value = false;
  }
};

</script>

<template>
  <header class="flex relative top-0 flex-row h-14 z-10 p-2 my-2 mx-4 justify-between items-center"
          style="border-radius: 2px; border: solid 1px hsl(225, 10%, 75%); background-color: rgb(247, 247, 248);">
    <div class="flex flex-row gap-x-2 items-center">
      <GradingButton v-tooltip.right="'Previous submission'" :icon="ArrowLeft" @click="previousSubmission"/>
      <Select v-model="selectedSubmission" :options="submissions" class="font-semibold w-64" filter
              optionLabel="filename" placeholder="Select a submission"/>
      <GradingButton v-tooltip.bottom="'Next submission'" :icon="ArrowRight" @click="nextSubmission"/>
      <GradingButton v-tooltip.bottom="'Upload submissions'" :icon="PlusIcon" @click="openUploadDialog"/>
    </div>
    
    <div class="flex flex-row gap-x-2 items-center">
      <GradingButton v-tooltip.left="'Export submissions'" :icon="FileDown" @click="exportDialogVisible = true"/>
    </div>
  </header>

  <ExportDialog v-model:visible="exportDialogVisible" :submissions="submissions"
                :current-submission="selectedSubmission"/>

  <Dialog v-model:visible="uploadDialogVisible" :style="{ width: '35rem' }" header="Upload Submissions" modal>
    <p class="mb-4 text-sm text-gray-600">Select one or more <strong>.bpmn</strong> files to upload as submissions.</p>
    <FileUpload
        accept=".bpmn"
        :multiple="true"
        :maxFileSize="10000000"
        customUpload
        :disabled="uploading"
        @uploader="handleUpload"
    >
      <template #empty>
        <span class="flex items-center justify-center flex-col gap-2 py-6">
          <i class="pi pi-cloud-upload text-4xl text-gray-400"></i>
          <p class="text-gray-500">Drag and drop .bpmn files here or click to browse.</p>
        </span>
      </template>
    </FileUpload>
  </Dialog>
</template>