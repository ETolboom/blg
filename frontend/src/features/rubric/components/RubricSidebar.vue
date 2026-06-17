<script lang="ts" setup>
import {computed, ref} from "vue";
import {Accordion, AccordionContent, AccordionHeader, AccordionPanel, Button} from "primevue";
import RubricCriterion from "@/features/rubric/components/RubricCriterion.vue";
import RubricGroup from "@/features/rubric/components/RubricGroup.vue";
import RubricScore from "@/features/rubric/components/RubricScore.vue";
import {CheckComplexity, CheckComplexityLabels} from "@/features/rubric/types/check_complexity.ts";
import {Criterion} from "@/features/rubric/types/rubric";
import RubricHeader from "@/features/rubric/components/RubricHeader.vue";
import {isGroup} from "@/features/behavior/types/group";

const props = withDefaults(defineProps<{
  criteria: Criterion[];
  correctScore: number;
  totalScore: number;
  correctPercentage: string;
  currentHighlightIndex: number;
  isEditable?: boolean;
  submissionFilename?: string;
  // True on the Reference tab: the criterion gear edits project-level thresholds.
  gradingReference?: boolean;
}>(), {
  isEditable: true,
  gradingReference: false,
});

const emit = defineEmits<{
  toggleHighlight: [index: number, problematicElements: string[]];
  toggleState: [index: number];
  resetCustomScore: [index: number];
  updatePoints: [index: number, points: Number];
  updateThreshold: [index: number, threshold: number | null, idealThreshold: number | null];
  updateProjectThreshold: [index: number, threshold: number | null, idealThreshold: number | null];
  updateNotes: [index: number, internalNotes: string | null, feedbackNotes: string | null];
  openAddDialog: [category: CheckComplexity];
  openBehavioralAddDialog: [];
  openAddGroupDialog: [];
  editCriterion: [criterion: Criterion];
  deleteCriterion: [criterionId: string];
}>();

const sidebarVisible = ref<boolean>(true);
const activeCategories = ref<CheckComplexity[]>([CheckComplexity.SIMPLE, CheckComplexity.CONFIGURABLE, CheckComplexity.COMPLEX]);

const groupByCategory = computed<Record<string, Criterion[]>>(() => {
  return props.criteria.reduce((acc, obj) => {
    (acc[obj.check_complexity] ||= []).push(obj);
    return acc;
  }, {} as Record<string, Criterion[]>);
});

const allCategories = computed(() => {
  return [CheckComplexity.SIMPLE, CheckComplexity.CONFIGURABLE, CheckComplexity.COMPLEX];
});

const handleAddCriteria = (category: CheckComplexity) => {
  if (category === CheckComplexity.COMPLEX) {
    emit('openBehavioralAddDialog');
  } else {
    emit('openAddDialog', category);
  }
};

const getCategoryItemCount = (category: CheckComplexity) => {
  return groupByCategory.value[category]?.length || 0;
};

const hasUngroupedComplexCriteria = computed(() => {
  const complexCriteria = groupByCategory.value[CheckComplexity.COMPLEX] || [];
  return complexCriteria.some(c => !isGroup(c));
});

const toggleSidebar = () => {
  sidebarVisible.value = !sidebarVisible.value;
};

</script>

<template>
  <div
      :class="sidebarVisible ? ['block'] : ['transition-transform duration-300 ease-in-out transform w-16 overflow-x-hidden']">
    <div class="flex flex-col bg-gray-100 w-[32rem] text-white h-full relative border-l border-gray-200">
      <RubricHeader
          :sidebar-visible="sidebarVisible"
          @toggle-sidebar="toggleSidebar"/>
        <div class="flex-auto overflow-y-auto py-2 px-2">
          <Accordion v-model:value="activeCategories" multiple>
            <AccordionPanel v-for="category in allCategories"
                            :key="category"
                            :value="category"
                            class="mb-3 rounded-lg overflow-hidden shadow-sm border border-gray-200 bg-white">
              <AccordionHeader>
                <div class="flex items-center justify-between w-full pr-2">
                  <div class="flex items-center gap-2">
                    <span class="font-semibold text-gray-700 uppercase text-sm">
                      {{ CheckComplexityLabels[category] }}
                    </span>
                    <span
                        v-if="getCategoryItemCount(category) > 0"
                        class="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded-full font-medium"
                    >
                      {{ getCategoryItemCount(category) }}
                    </span>
                  </div>
                  <div v-if="category === CheckComplexity.COMPLEX && !submissionFilename" class="flex gap-2">
                    <Button
                        class="!bg-transparent !border-0 !shadow-none !text-blue-500 hover:!text-blue-600 hover:-translate-y-0.5 transition-all duration-200"
                        icon="pi pi-plus"
                        label="Rule"
                        size="small"
                        text
                        @click.stop="emit('openBehavioralAddDialog')"
                    />
                    <Button
                        class="!bg-transparent !border-0 !shadow-none !text-blue-500 hover:!text-blue-600 hover:-translate-y-0.5 transition-all duration-200 disabled:!text-gray-400 disabled:hover:!text-gray-400 disabled:hover:!translate-y-0 disabled:cursor-not-allowed"
                        icon="pi pi-plus"
                        label="Group"
                        size="small"
                        text
                        :disabled="!hasUngroupedComplexCriteria"
                        @click.stop="emit('openAddGroupDialog')"
                    />
                  </div>
                  <Button
                      v-else-if="category !== CheckComplexity.COMPLEX && !submissionFilename"
                      class="!bg-transparent !border-0 !shadow-none !text-blue-500 hover:!text-blue-600 hover:-translate-y-0.5 transition-all duration-200"
                      icon="pi pi-plus"
                      label="Add"
                      size="small"
                      text
                      @click.stop="handleAddCriteria(category)"
                  />
                </div>
              </AccordionHeader>
              <AccordionContent>
                <div class="flex flex-col gap-2 pt-2">
                  <template v-if="groupByCategory[category] && groupByCategory[category].length > 0">
                    <template v-for="item in groupByCategory[category]" :key="item.name">
                      <RubricGroup
                        v-if="isGroup(item)"
                        :criterion="item"
                        :is-editable="isEditable"
                        :submission-filename="submissionFilename"
                        @editCriterion="(c) => emit('editCriterion', c)"
                        @toggleHighlight="(_index, elements) => emit('toggleHighlight', -1, elements)"
                        @delete="emit('deleteCriterion', item.id || '')"
                      />
                      <RubricCriterion
                        v-else
                        :category="item.check_complexity"
                        :class="currentHighlightIndex === criteria.indexOf(item) ? ' border-2 border-blue-500 shadow-md' : ' border border-gray-200'"
                        :custom_score_set="item.score != null"
                        :description="item.description"
                        :points="item.fulfilled ? (item.score ?? item.default_points) : 0"
                        :state="item.fulfilled"
                        :title="item.name"
                        :criterion="item"
                        :is-editable="isEditable"
                        :grading-submission="!!submissionFilename"
                        :grading-reference="gradingReference"
                        @click="emit('toggleHighlight', criteria.indexOf(item), item['problematic_elements'])"
                        @edit="emit('editCriterion', item)"
                        @reset="emit('resetCustomScore', criteria.indexOf(item))"
                        @toggle="emit('toggleState', criteria.indexOf(item))"
                        @updatePoints="(points: Number) => emit('updatePoints', criteria.indexOf(item), points)"
                        @updateThreshold="(t: number | null, i: number | null) => emit('updateThreshold', criteria.indexOf(item), t, i)"
                        @updateProjectThreshold="(t: number | null, i: number | null) => emit('updateProjectThreshold', criteria.indexOf(item), t, i)"
                        @updateNotes="(internal: string | null, feedback: string | null) => emit('updateNotes', criteria.indexOf(item), internal, feedback)"
                        @delete="emit('deleteCriterion', item.id || '')"
                      />
                    </template>
                  </template>


                  <div
                      v-else
                      class="text-center text-gray-500 text-sm py-6 bg-gray-50 rounded-lg border border-dashed border-gray-300"
                  >
                    <p>No criteria yet</p>
                    <p class="text-xs mt-1">Click "Add" to create your first criterion</p>
                  </div>
                </div>
              </AccordionContent>
            </AccordionPanel>
          </Accordion>
        </div>
      <RubricScore
          :correct-percentage="correctPercentage"
          :correct-score="correctScore"
          :total-score="totalScore"
      />
    </div>
  </div>
</template>

<style>
/* Style the entire AccordionHeader button including the chevron */
.p-accordionheader-toggle {
  background-color: #f9fafb !important;
  border-bottom: 1px solid #d1d5db !important;
  transition: background-color 0.2s ease !important;
  padding: 0.75rem !important;
}

.p-accordionheader-toggle:hover {
  background-color: #f3f4f6 !important;
}

.p-accordionheader {
  background-color: #f9fafb !important;
  border-bottom: 1px solid #d1d5db !important;
}

.p-accordionheader:hover {
  background-color: #f3f4f6 !important;
}

.p-accordion .p-accordionheader button {
  background-color: #f9fafb !important;
  border-bottom: 1px solid #d1d5db !important;
}

.p-accordion .p-accordionheader button:hover {
  background-color: #f3f4f6 !important;
}
</style>
