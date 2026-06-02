<template>
  <div>
    <h3 class="title is-5">Categories</h3>
    <b-field grouped>
      <b-input
        v-model="newName"
        placeholder="New category"
        maxlength="64"
        expanded
        @keyup.enter="add"
      />
      <b-button
        type="is-primary"
        size="is-small"
        icon-left="plus"
        class="add-btn"
        :disabled="!canAdd"
        @click="add"
      >
        Add
      </b-button>
    </b-field>

    <table class="table is-fullwidth is-striped">
      <thead>
        <tr>
          <th>Name</th>
          <th class="has-text-right">Sounds</th>
          <th class="has-text-right">Actions</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="c in categories.categories" :key="c.id">
          <td>{{ c.name }}</td>
          <td class="has-text-right">{{ c.sound_count }}</td>
          <td class="has-text-right">
            <b-button
              size="is-small"
              type="is-info"
              icon-left="pencil"
              class="mr-2"
              @click="openRename(c)"
            >
              Edit
            </b-button>
            <b-button size="is-small" type="is-danger" icon-left="trash" @click="deleting = c">
              Delete
            </b-button>
          </td>
        </tr>
        <tr v-if="!categories.categories.length">
          <td colspan="3" class="has-text-grey has-text-centered">
            No categories yet.
          </td>
        </tr>
      </tbody>
    </table>
    <p v-if="categories.error" class="has-text-danger">{{ categories.error }}</p>

    <ConfirmDialog
      v-if="deleting"
      title="Delete category"
      :message="deleteMessage"
      @confirm="confirmDelete"
      @close="deleting = null"
    />

    <RenameDialog
      v-if="renaming"
      title="Rename category"
      label="Category name"
      :initial="renaming.name"
      :maxlength="64"
      :error="renameError"
      :loading="renameLoading"
      @confirm="confirmRename"
      @close="closeRename"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import ConfirmDialog from "./ConfirmDialog.vue";
import RenameDialog from "./RenameDialog.vue";
import { useCategoriesStore } from "@/stores/categories";
import type { CategoryOut } from "@/api";

const categories = useCategoriesStore();
const newName = ref("");
const deleting = ref<CategoryOut | null>(null);
const renaming = ref<CategoryOut | null>(null);
const renameError = ref<string | null>(null);
const renameLoading = ref(false);

const deleteMessage = computed(() => {
  const c = deleting.value;
  if (!c) return "";
  const suffix = c.sound_count > 0
    ? ` ${c.sound_count} sound${c.sound_count === 1 ? "" : "s"} will become uncategorized.`
    : "";
  return `Delete category '${c.name}'?${suffix}`;
});

const canAdd = computed(() => newName.value.trim().length > 0);

onMounted(() => {
  // Refresh so counts are up-to-date when the tab is opened.
  void categories.refresh();
});

async function add(): Promise<void> {
  if (!canAdd.value) return;
  const ok = await categories.create(newName.value.trim());
  if (ok) newName.value = "";
}

async function confirmDelete(): Promise<void> {
  const c = deleting.value;
  if (!c) return;
  await categories.remove(c.id);
}

function openRename(c: CategoryOut): void {
  renaming.value = c;
  renameError.value = null;
}

function closeRename(): void {
  renaming.value = null;
  renameError.value = null;
  renameLoading.value = false;
}

async function confirmRename(newName: string): Promise<void> {
  const c = renaming.value;
  if (!c) return;
  renameLoading.value = true;
  const ok = await categories.rename(c.id, newName);
  renameLoading.value = false;
  if (ok) closeRename();
  else renameError.value = categories.error;
}
</script>

<style scoped>
/* Small button, but stretched to match the default-size input height
   so the row stays visually aligned. */
.add-btn {
  height: 3em;
}
</style>
