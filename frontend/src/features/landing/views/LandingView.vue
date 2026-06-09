<script lang="ts" setup>
import { onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { Button, Dialog, InputText, ProgressBar, useToast } from "primevue";
import { FolderOpen, Plus } from "lucide-vue-next";
import { ApiError, projectService } from "@/services";

const router = useRouter();
const toast = useToast();

const projects = ref<string[]>([]);
const isLoading = ref<boolean>(true);
const isBusy = ref<boolean>(false);
const createDialogVisible = ref<boolean>(false);
const newProjectName = ref<string>("");

const showError = (summary: string, error: unknown) => {
  const detail = error instanceof ApiError ? error.detail : String(error);
  toast.add({ severity: "error", summary, detail, life: 8000 });
};

const loadProjects = async () => {
  isLoading.value = true;
  try {
    projects.value = await projectService.getProjects();
  } catch (error) {
    showError("Could not load projects", error);
  } finally {
    isLoading.value = false;
  }
};

const openProject = async (name: string) => {
  if (isBusy.value) return;
  isBusy.value = true;
  try {
    await projectService.selectProject(name);
    await router.push("/grade");
  } catch (error) {
    showError("Could not open project", error);
    isBusy.value = false;
  }
};

const createProject = async () => {
  const name = newProjectName.value.trim();
  if (!name) return;
  isBusy.value = true;
  try {
    await projectService.createProject(name);
    createDialogVisible.value = false;
    await router.push("/grade");
  } catch (error) {
    showError("Could not create project", error);
    isBusy.value = false;
  }
};

onMounted(loadProjects);
</script>

<template>
  <div class="h-full w-full flex flex-col items-center justify-center bg-gray-50 p-8">
    <div class="w-full max-w-2xl">
      <div class="text-center mb-8">
        <h1 class="text-3xl font-bold text-gray-800">BPMN Learn &amp; Grade</h1>
        <p class="text-gray-500 mt-2">Select an assignment to start grading, or create a new one.</p>
      </div>

      <div class="bg-white border border-gray-200 rounded-lg shadow-sm">
        <div class="flex items-center justify-between px-5 py-3 border-b border-gray-200">
          <span class="font-semibold text-gray-700">Assignments</span>
          <Button label="New assignment" size="small" @click="createDialogVisible = true">
            <template #icon><Plus :size="16" class="mr-1" /></template>
          </Button>
        </div>

        <div v-if="isLoading" class="p-6">
          <ProgressBar mode="indeterminate" style="height: 0.4rem" />
        </div>

        <div v-else-if="projects.length === 0" class="p-10 text-center text-gray-500">
          <p>No assignments yet.</p>
          <p class="text-sm mt-1">Click "New assignment" to create your first one.</p>
        </div>

        <ul v-else class="divide-y divide-gray-100">
          <li
            v-for="name in projects"
            :key="name"
            class="flex items-center gap-3 px-5 py-3 cursor-pointer hover:bg-blue-50 transition-colors"
            :class="{ 'opacity-50 pointer-events-none': isBusy }"
            @click="openProject(name)"
          >
            <FolderOpen :size="20" class="text-blue-500 shrink-0" />
            <span class="font-medium text-gray-800">{{ name }}</span>
          </li>
        </ul>
      </div>
    </div>

    <Dialog v-model:visible="createDialogVisible" :style="{ width: '28rem' }" header="New assignment" modal>
      <div class="flex flex-col gap-2 mb-4">
        <label class="font-semibold" for="project-name">Name</label>
        <InputText
          id="project-name"
          v-model="newProjectName"
          class="w-full"
          placeholder="e.g. 2025"
          autofocus
          @keyup.enter="createProject"
        />
        <small class="text-gray-500">A folder is created under assignments/. You'll set up the rubric next.</small>
      </div>
      <div class="flex justify-end gap-2">
        <Button label="Cancel" severity="secondary" @click="createDialogVisible = false" />
        <Button label="Create" :disabled="!newProjectName.trim() || isBusy" @click="createProject" />
      </div>
    </Dialog>

    <Toast class="text-black" position="top-center" />
  </div>
</template>
