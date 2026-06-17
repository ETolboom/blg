<script lang="ts" setup>
import {computed, ref, watch} from "vue";
import {Button, Checkbox, Dialog, Listbox, RadioButton, Tag, useToast} from "primevue";
import {submissionService, toastError} from "@/services";
import type Submission from "@/features/grading/types/submission";

const props = defineProps<{
  submissions: Submission[];
  currentSubmission: Submission | null;
}>();

const visible = defineModel<boolean>("visible", {required: true});

const toast = useToast();

type Scope = "current" | "all" | "custom";

const scope = ref<Scope>("current");
const selected = ref<string[]>([]);
const includeThresholds = ref(true);
const includeInternalNotes = ref(true);
const includeFeedbackNotes = ref(true);
const exporting = ref(false);

const analyzedSubmissions = computed(() => props.submissions.filter((s) => s.analyzed));
const currentAnalyzed = computed(() => props.currentSubmission?.analyzed ?? false);
const hasUnanalyzed = computed(() => props.submissions.some((s) => !s.analyzed));

const submissionOptions = computed(() =>
    props.submissions.map((s) => ({
      filename: s.filename,
      name: s.name,
      disabled: !s.analyzed,
    }))
);

watch(visible, (isVisible) => {
  if (!isVisible) return;
  scope.value = currentAnalyzed.value ? "current" : "all";
  selected.value = [];
  includeThresholds.value = true;
  includeInternalNotes.value = true;
  includeFeedbackNotes.value = true;
});

const resolvedFilenames = computed<string[]>(() => {
  if (scope.value === "current") {
    return props.currentSubmission && currentAnalyzed.value
        ? [props.currentSubmission.filename]
        : [];
  }
  if (scope.value === "all") {
    return analyzedSubmissions.value.map((s) => s.filename);
  }
  return selected.value;
});

const canExport = computed(() => !exporting.value && resolvedFilenames.value.length > 0);

const exportNow = async () => {
  if (!canExport.value) return;
  exporting.value = true;
  try {
    await submissionService.exportSubmissions(
        resolvedFilenames.value,
        includeThresholds.value,
        includeInternalNotes.value,
        includeFeedbackNotes.value
    );
    visible.value = false;
  } catch (error) {
    console.error(error);
    toastError(toast, "Export failed", error, {fallback: "Could not export submissions."});
  } finally {
    exporting.value = false;
  }
};
</script>

<template>
  <Dialog v-model:visible="visible" :style="{ width: '32rem' }" modal>
    <template #header>
      <div class="flex flex-col gap-y-1">
        <span class="text-xl font-semibold">Export submissions</span>
        <p class="text-sm font-normal text-gray-600">
          Export submissions to an Excel sheet. If more than one submission is selected, each is
          added as a separate sheet.
        </p>
      </div>
    </template>

    <div class="flex flex-col gap-y-4">
      <div class="flex flex-col gap-y-2">
        <span class="text-sm font-semibold text-gray-700">What to export</span>

        <label class="flex items-center gap-x-2" :class="{ 'opacity-50': !currentAnalyzed }">
          <RadioButton v-model="scope" value="current" :disabled="!currentAnalyzed"/>
          <span>Current submission</span>
          <span v-if="currentSubmission && currentAnalyzed" class="text-sm text-gray-500">
            ({{ currentSubmission.name }})
          </span>
          <span v-else class="text-sm text-gray-500">(not analyzed)</span>
        </label>

        <label class="flex items-center gap-x-2">
          <RadioButton v-model="scope" value="all"/>
          <span>All analyzed submissions</span>
          <span class="text-sm text-gray-500">({{ analyzedSubmissions.length }})</span>
        </label>

        <label class="flex items-center gap-x-2">
          <RadioButton v-model="scope" value="custom"/>
          <span>Custom selection</span>
        </label>

        <Listbox v-if="scope === 'custom'"
                 v-model="selected"
                 class="ml-6 mt-1"
                 :options="submissionOptions"
                 optionLabel="name"
                 optionValue="filename"
                 optionDisabled="disabled"
                 multiple
                 checkmark
                 filter
                 filterPlaceholder="Search submissions"
                 scrollHeight="14rem"
                 emptyMessage="No submissions available."
                 emptyFilterMessage="No matching submissions.">
          <template #option="{ option }">
            <div class="flex items-center justify-between w-full gap-x-2">
              <span class="truncate">{{ option.name }}</span>
              <Tag v-if="option.disabled" value="not analyzed" severity="secondary"/>
            </div>
          </template>
        </Listbox>

        <p v-if="hasUnanalyzed" class="text-xs text-gray-500">
          Note: Submissions marked "not analyzed" have no grades yet and can't
          be exported. Open one in the grading view to analyze it first.
        </p>
      </div>

      <div class="flex flex-col gap-y-2 border-t border-gray-200 pt-3">
        <span class="text-sm font-semibold text-gray-700">Include</span>
        <label class="flex items-center gap-x-2">
          <Checkbox v-model="includeThresholds" binary/>
          <span>Custom thresholds</span>
        </label>
        <label class="flex items-center gap-x-2">
          <Checkbox v-model="includeInternalNotes" binary/>
          <span>Internal notes</span>
        </label>
        <label class="flex items-center gap-x-2">
          <Checkbox v-model="includeFeedbackNotes" binary/>
          <span>Feedback notes</span>
        </label>
      </div>
    </div>

    <template #footer>
      <Button label="Cancel" severity="secondary" text @click="visible = false"/>
      <Button label="Export" :disabled="!canExport" :loading="exporting" @click="exportNow"/>
    </template>
  </Dialog>
</template>
