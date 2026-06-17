<script lang="ts" setup>
import {onMounted, ref, watch} from "vue";
import {useToast, useConfirm} from "primevue";
import _ from "lodash";
import {type Check, checkService, rubricService, behavioralRuleService, submissionService, toastError, toastSuccess} from "@/services";
import RubricSidebar from "@/features/rubric/components/RubricSidebar.vue";
import RubricAlgorithmDialog from "@/features/rubric/components/RubricAlgorithmDialog.vue";
import {Criterion, Rubric} from "@/features/rubric/types/rubric";
import {CheckComplexity} from "@/features/rubric/types/check_complexity";
import BpmnModeler from "bpmn-js/lib/Modeler";
import {BehavioralRule} from "@/features/behavior/types/template.ts";
import RubricBehavioralDialog from "@/features/rubric/components/RubricBehavioralDialog.vue";
import RubricGroupDialog from "@/features/rubric/components/RubricGroupDialog.vue";
import {BehavioralRuleGroup} from "@/features/behavior/types/group";
import {groupService} from "@/services/groupService";

const props = defineProps<{
  modeler: BpmnModeler;
  criteria: Criterion[];
  isEditable?: boolean;
  submissionName?: string;
  // True on the Reference tab: the criterion gear edits project-level thresholds.
  gradingReference?: boolean;
}>();

const emit = defineEmits<{
  updateRubric: [rubric: Rubric];
  saveSubmission: [criteria: Criterion[]];
}>();

const toast = useToast();
const confirm = useConfirm();

const totalScore = ref<number>(0);
const correctPercentage = ref<string>("0.0");
const correctScore = ref<number>(0);
const currentHighlightIndex = ref<number>(-1);
const currentHighlightElements = ref<string[]>([]);
const availableChecks = ref<Check[] | null>(null);
const availableRules = ref<BehavioralRule[] | null>(null);
const availableTemplates = ref<BehavioralRule[] | null>(null);
const addDialogVisible = ref<boolean>(false);
const behavioralAddDialogVisible = ref<boolean>(false);
const groupAddDialogVisible = ref<boolean>(false);
const addDialogType = ref<CheckComplexity | null>(null);
const editingCheck = ref<Check | null>(null);

const calculateScore = (): void => {
  let total = 0;
  let correct = 0;
  props.criteria.forEach((item) => {
    total += item['default_points'];
    correct += item.fulfilled ? (item.score ?? item['default_points']) : 0;
  });

  totalScore.value = total;
  correctScore.value = correct;
  correctPercentage.value = total > 0 ? ((correct / total) * 100).toFixed(2) : "0.00";
};

const toggleState = (index: number): void => {
  const criterion = props.criteria[index];
  if (!criterion) return;

  criterion.fulfilled = !criterion.fulfilled;
  if (!criterion.fulfilled) criterion.score = null;
  emit('saveSubmission', props.criteria);
  calculateScore();
};

// Highlight via bpmn-js's own marker API (a CSS class on the element group)
// instead of reaching into its SVG; see the `.bpmn-highlight` rule below.
const HIGHLIGHT_MARKER = 'bpmn-highlight';

const clearHighlight = (): void => {
  const canvas = props.modeler.get('canvas');
  for (const id of currentHighlightElements.value) {
    canvas.removeMarker(id, HIGHLIGHT_MARKER);
  }
  currentHighlightElements.value = [];
  currentHighlightIndex.value = -1;
};

const toggleHighlight = (index: number, problematicElements: string[]): void => {
  // If clicking the same criterion, deselect it
  if (currentHighlightIndex.value === index) {
    clearHighlight();
    return;
  }

  // Clear any previous highlight before applying the new one
  clearHighlight();

  const canvas = props.modeler.get('canvas');
  const elementRegistry = props.modeler.get('elementRegistry');
  const applied: string[] = [];
  for (const id of problematicElements) {
    // The element may not exist in the currently-loaded diagram (e.g. wrong tab)
    if (!elementRegistry.get(id)) continue;
    canvas.addMarker(id, HIGHLIGHT_MARKER);
    applied.push(id);
  }

  currentHighlightIndex.value = index;
  currentHighlightElements.value = applied;
};



const fetchAvailableChecks = async (): Promise<void> => {
  try {
    availableChecks.value = await checkService.getChecks();
  } catch (error) {
    toastError(toast, 'Could not load checks', error);
  }
};

const fetchAvailableRules = async (): Promise<void> => {
  try {
    availableRules.value = await behavioralRuleService.getBehavioralRules();
  } catch (error) {
    toastError(toast, 'Could not load rules', error);
    availableRules.value = [];
  }
};

const fetchAvailableTemplates = async (): Promise<void> => {
  try {
    availableTemplates.value = await behavioralRuleService.getBehavioralRuleTemplates();
  } catch (error) {
    toastError(toast, 'Could not load templates', error);
    availableTemplates.value = [];
  }
};



const updatePoints = (index: number, score: string): void => {
  const criterion = props.criteria[index];
  if (!criterion) return;

  const n = Number(score);
  if (Number.isNaN(n) || n <= 0) {
    criterion.score = null;
    criterion.fulfilled = false;
  } else if (n === criterion.default_points) {
    criterion.score = null;
    criterion.fulfilled = true;
  } else {
    criterion.score = n;
    criterion.fulfilled = true;
  }
  emit('saveSubmission', props.criteria);
  calculateScore();
};

const resetCustomScore = (index: number): void => {
  const criterion = props.criteria[index];
  if (!criterion) return;

  criterion.score = null;
  criterion.fulfilled = false;
  emit('saveSubmission', props.criteria);
  calculateScore();
};

const updateThreshold = async (
    index: number,
    threshold: number | null,
    idealThreshold: number | null,
): Promise<void> => {
  const criterion = props.criteria[index];
  if (!criterion || !props.submissionName) return;

  try {
    const rubric = await submissionService.regradeCriterionThreshold(
        props.submissionName, criterion.id, threshold, idealThreshold
    );
    emit('updateRubric', rubric);
    const reset = threshold === null && idealThreshold === null;
    toastSuccess(toast, 'Criterion re-graded', {
      message: reset ? 'Thresholds reset to defaults' : 'Re-graded with new thresholds',
    });
  } catch (error) {
    toastError(toast, 'Could not re-grade criterion', error);
  }
};

const updateProjectThreshold = async (
    index: number,
    threshold: number | null,
    idealThreshold: number | null,
): Promise<void> => {
  const criterion = props.criteria[index];
  if (!criterion) return;

  try {
    const rubric = await rubricService.updateCriterionProjectThreshold(
        criterion.id, threshold, idealThreshold
    );
    emit('updateRubric', rubric);
    const reset = threshold === null && idealThreshold === null;
    toastSuccess(toast, 'Assignment matching threshold updated', {
      message: reset
          ? 'Reset to the global default; reference and submissions re-graded'
          : 'Reference and inheriting submissions re-graded',
    });
  } catch (error) {
    toastError(toast, 'Could not update assignment matching threshold', error);
  }
};

const updateNotes = (
    index: number,
    internalNotes: string | null,
    feedbackNotes: string | null,
): void => {
  const criterion = props.criteria[index];
  if (!criterion) return;

  criterion.internal_notes = internalNotes;
  criterion.feedback_notes = feedbackNotes;
  emit('saveSubmission', props.criteria);
};

const openAddDialog = (category: CheckComplexity): void => {
  addDialogType.value = category;
  editingCheck.value = null;
  addDialogVisible.value = true;
};

const openBehavioralAddDialog = (): void => {
  behavioralAddDialogVisible.value = true;
};

const openGroupAddDialog = (): void => {
  groupAddDialogVisible.value = true;
};


const handleSaveRubric = async (check: Check): Promise<void> => {
  try {
    const data = await rubricService.updateCheckCriterion(check);
    emit("updateRubric", data);
    const message = editingCheck.value
        ? "Check criterion updated successfully."
        : "Check criterion added successfully.";
    toast.add({
      severity: 'success',
      summary: 'Rubric',
      detail: message,
      life: 5000
    });
    addDialogVisible.value = false;
    editingCheck.value = null;
  } catch (error) {
    toastError(toast, 'Rubric', error, { life: 10000 });
  }
};

const handleNewBehavorialRule = async (rule: BehavioralRule): Promise<void> => {
  try {
    const data = await rubricService.updateBehavioralCriterion(rule);
    emit("updateRubric", data);
    toast.add({severity: 'success', summary: 'Rubric', detail: "Behavioral criterion added successfully.", life: 5000});
    behavioralAddDialogVisible.value = false;

    // Navigate to behavior editor with rule ID
    window.open(`/behavior/${rule.id}`, '_blank');
  } catch (error) {
    toastError(toast, 'Rubric', error, { life: 10000 });
  }
};

const handleSaveGroup = async (group: BehavioralRuleGroup): Promise<void> => {
  try {
    // Add group to rubric
    const data = await groupService.addGroupToRubric(group);
    emit("updateRubric", data);
    
    toast.add({
      severity: 'success', 
      summary: 'Rubric', 
      detail: `Group "${group.name}" added successfully.`, 
      life: 5000
    });
    
    groupAddDialogVisible.value = false;
  } catch (error) {
    toastError(toast, 'Rubric', error, { life: 10000 });
  }
};

const handleDeleteCriterion = (criterionId: string): void => {
  if (!criterionId) return;

  confirm.require({
    message: "Are you sure you want to delete this criterion?",
    header: "Delete criterion",
    icon: "pi pi-exclamation-triangle",
    rejectProps: { label: "Cancel", severity: "secondary", outlined: true },
    acceptProps: { label: "Delete", severity: "danger" },
    accept: async () => {
      try {
        const data = await rubricService.deleteCriterion(criterionId);

        // Refresh rubric
        const rubric = await rubricService.getRubric();
        emit("updateRubric", rubric);

        toastSuccess(toast, 'Rubric', data, { life: 5000 });

        if (data.unmerged_rules && data.unmerged_rules.length > 0) {
          toast.add({
            severity: 'info',
            summary: 'Unmerged',
            detail: `Restored rules: ${data.unmerged_rules.join(', ')}`,
            life: 7000
          });
        }

        if (data.warning) {
          toast.add({
            severity: 'warn',
            summary: 'Warning',
            detail: data.warning,
            life: 10000
          });
        }
      } catch (error) {
        toastError(toast, 'Rubric', error, { life: 10000 });
      }
    }
  });
};




const handleEditCriterion = (criterion: Criterion): void => {
  if (criterion.check_complexity === CheckComplexity.COMPLEX) {
    // Navigate to behavior editor with rule ID
    const url = props.submissionName 
        ? `/behavior/${criterion.id}?submission=${encodeURIComponent(props.submissionName)}`
        : `/behavior/${criterion.id}`;
    window.open(url, '_blank');
  } else {
    // It's a check criterion, open the edit dialog (a Criterion is a Check).
    editingCheck.value = criterion;
    addDialogType.value = criterion.check_complexity;
    addDialogVisible.value = true;
  }
};

watch(
    () => props.criteria,
    () => calculateScore(),
    {deep: true}
);



watch(addDialogVisible, (newValue) => {
  if (!newValue) {
    // Clear editing state when dialog is closed
    editingCheck.value = null;
  }
});

onMounted(() => {
  calculateScore();
  fetchAvailableChecks();
  fetchAvailableRules();
  fetchAvailableTemplates();
});

</script>

<template>
  <RubricAlgorithmDialog
      v-model:visible="addDialogVisible"
      :available-checks="availableChecks"
      :category="addDialogType"
      :existing-criteria="criteria.filter(c => c.check_complexity !== CheckComplexity.COMPLEX)"
      :editing-check="editingCheck"
      @save="handleSaveRubric"
  />
  <RubricBehavioralDialog
      v-model:visible="behavioralAddDialogVisible"
      :available-templates="availableTemplates || []"
      @save="handleNewBehavorialRule"
  />
  <RubricGroupDialog
      v-model:visible="groupAddDialogVisible"
      :available-rules="availableRules || []"
      :existing-criteria="criteria"
      @save="handleSaveGroup"
  />


  <RubricSidebar
      :correct-percentage="correctPercentage"
      :correct-score="correctScore"
      :criteria="criteria"
      :current-highlight-index="currentHighlightIndex"
      :total-score="totalScore"
      :is-editable="isEditable"
      :submission-filename="submissionName"
      :grading-reference="gradingReference"
      @open-add-dialog="openAddDialog"
      @open-behavioral-add-dialog="openBehavioralAddDialog"
      @open-add-group-dialog="openGroupAddDialog"
      @reset-custom-score="resetCustomScore"
      @toggle-highlight="toggleHighlight"
      @toggle-state="toggleState"
      @update-points="(index, score) => updatePoints(index, String(score))"
      @update-threshold="updateThreshold"
      @update-project-threshold="updateProjectThreshold"
      @update-notes="updateNotes"
      @edit-criterion="handleEditCriterion"
      @delete-criterion="handleDeleteCriterion"
  />
</template>

<style scoped>
</style>

<!-- Global (unscoped): bpmn-js renders its SVG outside this component's tree, and
     the `bpmn-highlight` marker class is added by canvas.addMarker (see toggleHighlight). -->
<style>
.djs-element.bpmn-highlight .djs-outline {
  visibility: visible !important;
  stroke: #ef4444 !important; /* tailwind red-500 */
  fill: none;
}
</style>
