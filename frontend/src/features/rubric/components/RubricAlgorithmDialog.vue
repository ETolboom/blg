<script lang="ts" setup>
import {ref, watch} from "vue";
import {Button, Dialog, InputText, Select} from "primevue";
import type {Check, CheckInput} from "@/services";
import {CheckComplexity} from "@/features/rubric/types/check_complexity.ts";

const props = defineProps<{
  visible: boolean;
  category: CheckComplexity | null;
  availableChecks: Check[] | null;
  existingCriteria?: Check[];
  editingCheck?: Check | null;
}>();

const emit = defineEmits<{
  'update:visible': [visible: boolean];
  save: [check: Check];
}>();

const selectedCheck = ref<Check | null>(null);
const workingCheck = ref<Check | null>(null);

const inputAt = (configIndex: number): CheckInput | undefined =>
    workingCheck.value?.inputs?.[configIndex];

const addKeyValueItem = (configIndex: number): void => {
  const input = inputAt(configIndex);
  if (input?.input_type !== 'key-value') return;
  input.data.pairs.push({key: '', value: ['']});
};

const removeKeyValueItem = (configIndex: number, itemIndex: number): void => {
  const input = inputAt(configIndex);
  if (input?.input_type !== 'key-value') return;
  if (input.data.pairs.length > 1) {
    input.data.pairs.splice(itemIndex, 1);
  }
};

const addStringItem = (configIndex: number): void => {
  const input = inputAt(configIndex);
  if (input?.input_type !== 'string' || !Array.isArray(input.data)) return;
  input.data.push('');
};

const addValueItem = (configIndex: number, itemIndex: number): void => {
  const input = inputAt(configIndex);
  if (input?.input_type !== 'key-value') return;
  input.data.pairs[itemIndex]?.value.push('');
};

const removeValueItem = (configIndex: number, itemIndex: number, valueIndex: number): void => {
  const input = inputAt(configIndex);
  if (input?.input_type !== 'key-value') return;
  const pair = input.data.pairs[itemIndex];
  if (pair && pair.value.length > 1) {
    pair.value.splice(valueIndex, 1);
  }
};

const addSelectionItem = (configIndex: number): void => {
  const input = inputAt(configIndex);
  if (input?.input_type !== 'selection') return;
  input.data.pairs.push({label: '', type: ''});
};

const removeSelectionItem = (configIndex: number, itemIndex: number): void => {
  const input = inputAt(configIndex);
  if (input?.input_type !== 'selection') return;
  if (input.data.pairs.length > 1) {
    input.data.pairs.splice(itemIndex, 1);
  }
};

const formatDisplayValue = (value: string): string => {
  // Special case for abstract task
  if (value === 'task') {
    return 'Abstract Task';
  }
  // Convert camelCase to Title Case (e.g., "serviceTask" -> "Service Task")
  return value
      .replace(/([A-Z])/g, ' $1')
      .replace(/^./, (str) => str.toUpperCase())
      .trim();
};

const filterByType = (category: CheckComplexity | null): Check[] => {
  if (!props.availableChecks || !props.category) return [];

  // Filter by category
  let filtered = props.availableChecks.filter(item => item.check_complexity === category);

  // Filter out checks that already exist in the rubric (only if not editing)
  if (props.existingCriteria && !props.editingCheck) {
    const existingIds = new Set(props.existingCriteria.map(c => c.id));
    filtered = filtered.filter(check => !existingIds.has(check.id));
  }

  return filtered;
};

const handleSave = (): void => {
  if (!workingCheck.value) return;

  // Create a deep copy of the working check
  const checkCopy: Check = JSON.parse(JSON.stringify(workingCheck.value));

  emit('save', checkCopy);
};

const handleClose = (): void => {
  emit('update:visible', false);
};

watch(() => props.visible, (newValue) => {
  if (newValue) {
    // If editing, pre-fill with the editing check
    if (props.editingCheck) {
      selectedCheck.value = props.editingCheck;
      // Create a working copy with the existing data
      workingCheck.value = JSON.parse(JSON.stringify(props.editingCheck));
    } else {
      selectedCheck.value = null;
      workingCheck.value = null;
    }
  }
});

watch(selectedCheck, (newCheck) => {
  if (!newCheck || !newCheck.inputs) {
    workingCheck.value = null;
    return;
  }

  // If we're editing and the check already has data, don't reinitialize
  if (props.editingCheck && newCheck.id === props.editingCheck.id) {
    return;
  }

  // Create a working copy with initialized data fields
  const copy: Check = JSON.parse(JSON.stringify(newCheck));

  if (copy.inputs) {
    copy.inputs.forEach(inputConfig => {
      if (inputConfig.input_type === 'key-value') {
        // Keep the scheme's labels; just seed one editable pair to start from.
        inputConfig.data.pairs = [{key: '', value: ['']}];
      } else if (inputConfig.input_type === 'string') {
        inputConfig.data = inputConfig.multiple ? [''] : '';
      } else if (inputConfig.input_type === 'integer') {
        inputConfig.data = inputConfig.multiple ? [0] : 0;
      } else if (inputConfig.input_type === 'selection') {
        // Initialize with one empty pair if pairs is empty
        if (inputConfig.data.pairs.length === 0) {
          inputConfig.data.pairs = [{label: '', type: ''}];
        }
      }
    });
  }

  workingCheck.value = copy;
});
</script>

<template>
  <Dialog
      :style="{ width: '36rem' }"
      :visible="visible"
      :header="editingCheck ? 'Edit rubric criteria' : 'Add rubric criteria'"
      modal
      @update:visible="handleClose">
    <div class="flex items-center gap-4 mb-4">
      <label class="font-semibold w-24" for="check-select">Check</label>
      <Select
          id="check-select"
          v-model="selectedCheck"
          :options="filterByType(category)"
          :disabled="!!editingCheck"
          class="flex-auto"
          option-label="name"
          placeholder="Select a check"/>
    </div>
    <div v-if="workingCheck?.inputs">
      <div v-if="workingCheck.inputs.length === 0">
        <span class="font-medium text-lg">This check has no available inputs</span>
      </div>
      <div v-for="(inputConfig, configIndex) in workingCheck.inputs" v-else :key="'form-container-' + configIndex"
           class="mb-4">
        <div v-if="inputConfig.input_type === 'key-value'">
          <label class="font-semibold block mb-2">{{ inputConfig['input_label'] }}</label>
          <div v-for="(pair, pairIndex) in inputConfig.data.pairs" :key="pairIndex"
               class="mb-4 p-3 border border-gray-200 rounded-lg relative">
            <div class="flex flex-col gap-3 mb-2">
              <InputText v-model="pair.key" :placeholder="inputConfig.data.key_label" class="flex-auto"/>
              <div v-for="(_, valueIndex) in pair.value" :key="valueIndex" class="flex gap-3">
                <InputText v-model="pair.value[valueIndex]" :placeholder="inputConfig.data.value_label"
                           class="flex-auto"/>
                <Button :disabled="pair.value.length <= 1" icon="pi pi-trash" rounded severity="danger" text
                        @click="removeValueItem(configIndex, pairIndex, valueIndex)"></Button>
              </div>
            </div>
            <div class="flex justify-content-end">
              <Button icon="pi pi-plus" label="Add Value" severity="secondary" text
                      @click="addValueItem(configIndex, pairIndex)"></Button>
            </div>
            <div v-if="inputConfig.multiple" class="flex justify-content-end mt-2">
              <Button :disabled="inputConfig.data.pairs.length <= 1" icon="pi pi-trash" label="Remove Pair" severity="danger" text
                      @click="removeKeyValueItem(configIndex, pairIndex)"></Button>
            </div>
          </div>
          <div v-if="inputConfig.multiple" class="flex justify-content-end">
            <Button icon="pi pi-plus" label="Add Pair" severity="secondary" text
                    @click="addKeyValueItem(configIndex)"></Button>
          </div>
        </div>
        <div v-else-if="inputConfig.input_type === 'string'">
          <label :for="'input-' + configIndex" class="font-semibold block mb-2">{{ inputConfig['input_label'] }}</label>
          <div v-if="inputConfig.multiple && Array.isArray(inputConfig.data)">
            <div v-for="(_, valueIndex) in inputConfig.data" :key="valueIndex" class="flex mb-2 gap-3">
              <InputText v-model="inputConfig.data[valueIndex]" class="flex-auto"></InputText>
              <Button :disabled="inputConfig.data.length <= 1" icon="pi pi-trash" rounded severity="danger" text
                      @click="inputConfig.data.splice(valueIndex, 1)"></Button>
            </div>
            <div class="flex justify-content-end">
              <Button icon="pi pi-plus" label="Add Another" severity="secondary" text
                      @click="addStringItem(configIndex)"></Button>
            </div>
          </div>
          <div v-else-if="!Array.isArray(inputConfig.data)" class="flex mb-4 gap-3 rounded-lg relative">
            <InputText :id="'input-' + configIndex" v-model="inputConfig.data"
                       class="flex-auto"></InputText>
          </div>
        </div>
        <div v-else-if="inputConfig.input_type === 'selection'">
          <label class="font-semibold block mb-2">{{ inputConfig['input_label'] }}</label>
          <div v-for="(pair, pairIndex) in inputConfig.data.pairs" :key="pairIndex"
               class="mb-4 p-3 border border-gray-200 rounded-lg relative">
            <div class="flex flex-col gap-3">
              <div class="flex items-center gap-2">
                <label class="font-medium w-32">Task Label:</label>
                <InputText v-model="pair.label" placeholder="Enter label" class="flex-auto"/>
              </div>
              <div class="flex items-center gap-2">
                <label class="font-medium w-32">Label Type:</label>
                <div class="flex-auto flex flex-col gap-1">
                  <Select
                      v-model="pair.type"
                      :options="inputConfig.data.accepted_values"
                      :placeholder="inputConfig.data.placeholder"
                      :class="{'border-orange-500': pair.type === 'task'}"
                      class="w-full">
                    <template #option="slotProps">
                      {{ formatDisplayValue(slotProps.option) }}
                    </template>
                    <template #value="slotProps">
                      <span v-if="slotProps.value">{{ formatDisplayValue(slotProps.value) }}</span>
                      <span v-else>{{ slotProps.placeholder }}</span>
                    </template>
                  </Select>
                  <small v-if="pair.type === 'task'" class="text-orange-500">
                    <i class="pi pi-exclamation-triangle"></i> Please select a specific task type
                  </small>
                </div>
              </div>
            </div>
            <div v-if="inputConfig.multiple" class="flex justify-content-end mt-2">
              <Button :disabled="inputConfig.data.pairs.length <= 1" icon="pi pi-trash" label="Remove" severity="danger" text
                      @click="removeSelectionItem(configIndex, pairIndex)"></Button>
            </div>
          </div>
          <div v-if="inputConfig.multiple" class="flex justify-content-end">
            <Button icon="pi pi-plus" label="Add Label" severity="secondary" text
                    @click="addSelectionItem(configIndex)"></Button>
          </div>
        </div>
      </div>
    </div>
    <div class="flex justify-end gap-2">
      <Button label="Cancel" severity="secondary" type="button" @click="handleClose"></Button>
      <Button label="Save" type="button" @click="handleSave"></Button>
    </div>
  </Dialog>
</template>

<style scoped>
</style>
