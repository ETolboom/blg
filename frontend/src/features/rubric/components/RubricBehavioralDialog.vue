<script lang="ts" setup>
import {computed, ref, watch} from "vue";
import {Button, Dialog, InputText, Select, Textarea} from "primevue";
import {BehavioralRule} from "@/features/behavior/types/template.ts";

const props = defineProps<{
  visible: boolean;
  availableTemplates: BehavioralRule[];
}>();

const emit = defineEmits<{
  'update:visible': [visible: boolean];
  save: [rule: BehavioralRule];
}>();

const NO_TEMPLATE = {name: 'No Template', id: '__no_template__'} as const;

// The Select offers the "No Template" sentinel alongside the real rules.
type TemplateOption = BehavioralRule | typeof NO_TEMPLATE;
const isNoTemplate = (t: TemplateOption): t is typeof NO_TEMPLATE => t.id === NO_TEMPLATE.id;

const selectedTemplate = ref<TemplateOption>(NO_TEMPLATE);
const customName = ref<string>('');
const customDescription = ref<string>('');

const templateOptions = computed<TemplateOption[]>(() => {
  return [NO_TEMPLATE, ...props.availableTemplates];
});

const isNoTemplateSelected = computed(() => isNoTemplate(selectedTemplate.value));

const isFormValid = computed(() => {
  return customName.value.trim().length > 0 && customDescription.value.trim().length > 0;
});

const generateIdFromName = (name: string): string => {
  return name
      .toLowerCase()
      .trim()
      .replace(/\s+/g, '_')
      .replace(/[^a-z0-9-_]/g, '');
};

const handleSave = (): void => {
  if (!isFormValid.value) return;

  const template = selectedTemplate.value;
  const ruleToSave: BehavioralRule = {
    id: generateIdFromName(customName.value),
    name: customName.value.trim(),
    description: customDescription.value.trim(),
    maxPoints: 0,
    nodes: isNoTemplate(template) ? [] : (template.nodes || []),
    edges: isNoTemplate(template) ? [] : (template.edges || [])
  };

  emit('save', ruleToSave);
};

const handleClose = (): void => {
  emit('update:visible', false);
};

watch(() => props.visible, (newValue) => {
  if (newValue) {
    selectedTemplate.value = NO_TEMPLATE;
    customName.value = '';
    customDescription.value = '';
  }
});

watch(selectedTemplate, (newTemplate: TemplateOption): void => {
  if (isNoTemplate(newTemplate)) {
    customName.value = '';
    customDescription.value = '';
    return;
  }

  customName.value = newTemplate.name || '';
  customDescription.value = newTemplate.description || '';
});
</script>

<template>
  <Dialog
      :style="{ width: '36rem' }"
      :visible="visible"
      header="Add behavioral rule"
      modal
      @update:visible="handleClose">
    <div class="flex items-center gap-4 mb-4">
      <label class="font-semibold w-24" for="template-select">Template</label>
      <Select
          id="template-select"
          v-model="selectedTemplate"
          :options="templateOptions"
          class="flex-auto"
          option-label="name"
          placeholder="Select a template"/>
    </div>
    <div class="space-y-4 mb-4">
      <div class="flex flex-col gap-2">
        <label class="font-semibold" for="custom-name">
          Name <span class="text-red-500">*</span>
        </label>
        <InputText
            id="custom-name"
            v-model="customName"
            class="w-full"
            placeholder="Enter rule name"/>
      </div>
      <div class="flex flex-col gap-2">
        <label class="font-semibold" for="custom-description">
          Description <span class="text-red-500">*</span>
        </label>
        <Textarea
            id="custom-description"
            v-model="customDescription"
            class="w-full"
            placeholder="Enter rule description"
            rows="4"/>
      </div>
    </div>
    <div class="flex justify-end gap-2">
      <Button label="Cancel" severity="secondary" type="button" @click="handleClose"></Button>
      <Button :disabled="!isFormValid" label="Save" type="button" @click="handleSave"></Button>
    </div>
  </Dialog>
</template>

<style scoped>
</style>
