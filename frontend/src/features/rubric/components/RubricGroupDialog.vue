<script lang="ts" setup>
import { ref, watch, computed } from "vue";
import { Button, Dialog, InputText, MultiSelect, RadioButton, useConfirm } from "primevue";

import type { BehavioralRule } from "@/features/behavior/types/template";
import type { BehavioralRuleGroup, GroupCondition } from "@/features/behavior/types/group";
import type { Criterion } from "@/features/rubric/types/rubric";
import { CheckComplexity } from "@/features/rubric/types/check_complexity";

const props = defineProps<{
  visible: boolean;
  availableRules: BehavioralRule[];
  existingCriteria?: Criterion[];
}>();

const emit = defineEmits<{
  'update:visible': [visible: boolean];
  'save': [group: BehavioralRuleGroup];
}>();

const confirm = useConfirm();

const groupId = ref('');
const name = ref('');
const condition = ref<GroupCondition>('XOR');
const selectedRules = ref<BehavioralRule[]>([]);

const groupOptions = computed(() => {
  if (!props.existingCriteria) return [];
  // Filter for COMPLEX (Behavioral) rules and exclude groups
  return props.existingCriteria.filter(c =>
    c.check_complexity === CheckComplexity.COMPLEX &&
    !c.id?.startsWith('group:')
  );
});

// Reset form when dialog opens
watch(() => props.visible, (newValue) => {
  if (newValue) {
    groupId.value = '';
    name.value = '';
    condition.value = 'XOR';
    selectedRules.value = [];
  }
});

// Auto-generate ID from name if ID is empty
const generateIdFromName = (name: string): string => {
  return name
    .toLowerCase()
    .trim()
    .replace(/\s+/g, '_')
    .replace(/[^a-z0-9-_]/g, '');
};

watch(name, (newName) => {
  groupId.value = generateIdFromName(newName);
});

const emitGroup = () => {
  const group: BehavioralRuleGroup = {
    group_id: groupId.value,
    name: name.value,
    condition: condition.value,
    rule_ids: selectedRules.value.map(t => t.id),
    rule_results: []
  };

  emit('save', group);
  emit('update:visible', false);
};

const handleSave = () => {
  // Validation
  if (!groupId.value || !name.value || !selectedRules.value.length) {
    return;
  }

  // Check for consumption
  const rulesToConsume = (props.existingCriteria ?? [])
    .filter(c => selectedRules.value.some(t => t.id === c.id))
    .map(c => c.name);

  if (rulesToConsume.length > 0) {
    confirm.require({
      header: 'Merge rules into group',
      message:
        `Creating this group will consume these individual rules: ${rulesToConsume.join(', ')}. ` +
        `They will be removed from the rubric list and merged into this group. Continue?`,
      icon: 'pi pi-exclamation-triangle',
      rejectProps: { label: 'Cancel', severity: 'secondary', outlined: true },
      acceptProps: { label: 'Merge' },
      accept: emitGroup
    });
    return;
  }

  emitGroup();
};

const handleClose = () => {
  emit('update:visible', false);
};
</script>

<template>
  <Dialog
    :visible="visible"
    :style="{ width: '40rem' }"
    header="Create Rule Group"
    modal
    @update:visible="handleClose"
  >
    <div class="space-y-4 mb-4">
      <div class="flex flex-col gap-2">
        <label class="font-semibold" for="group-name">Name</label>
        <InputText
          id="group-name"
          v-model="name"
          class="w-full"
          placeholder="e.g., Part 1 - Residency Check"
        />
      </div>



      <div class="flex flex-col gap-2">
        <label class="font-semibold">Condition</label>
        <div class="flex gap-4">
          <div class="flex items-center gap-2">
            <RadioButton v-model="condition" inputId="xor" value="XOR" />
            <label for="xor" class="cursor-pointer">
              <span class="font-bold text-blue-500">XOR</span> - Alternative Solutions
            </label>
          </div>
          <div class="flex items-center gap-2">
            <RadioButton v-model="condition" inputId="and" value="AND" />
            <label for="and" class="cursor-pointer">
              <span class="font-bold text-green-500">AND</span> - Required Features
            </label>
          </div>
        </div>
        <small class="text-gray-500" v-if="condition === 'XOR'">
          Students score the MAX points from the best matching rule.
        </small>
        <small class="text-gray-500" v-if="condition === 'AND'">
          Students must match ALL rules to get points.
        </small>
      </div>

      <div class="flex flex-col gap-2">
        <label class="font-semibold" for="group-rules">Rules</label>
        <MultiSelect
          id="group-rules"
          v-model="selectedRules"
          :options="groupOptions"
          optionLabel="name"
          placeholder="Select rules"
          display="chip"
          class="w-full"
          filter
        />
      </div>
    </div>

    <div class="flex justify-end gap-2">
      <Button label="Cancel" severity="secondary" @click="handleClose" />
      <Button label="Create Group" @click="handleSave" :disabled="!name || !selectedRules.length" />
    </div>
  </Dialog>
</template>
