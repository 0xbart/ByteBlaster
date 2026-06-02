<template>
  <div>
    <div class="header-row">
      <h3 class="title is-5 mb-0">Tags</h3>
      <span class="has-text-grey ml-3">{{ tags.tags.length }} total</span>
    </div>
    <p class="has-text-grey is-size-7 mb-3">
      Tags are created automatically when uploading or editing a sound.
      Deleting a tag here removes it from all sounds.
    </p>

    <table class="table is-fullwidth is-striped">
      <thead>
        <tr>
          <th>Name</th>
          <th class="has-text-right">Sounds</th>
          <th class="has-text-right">Actions</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="t in tags.tags" :key="t.id">
          <td><span class="tag is-light">#{{ t.name }}</span></td>
          <td class="has-text-right">{{ t.sound_count }}</td>
          <td class="has-text-right">
            <b-button
              size="is-small"
              type="is-info"
              icon-left="pencil"
              class="mr-2"
              @click="openRename(t)"
            >
              Edit
            </b-button>
            <b-button size="is-small" type="is-danger" icon-left="delete" @click="deleting = t">
              Delete
            </b-button>
          </td>
        </tr>
        <tr v-if="!tags.tags.length">
          <td colspan="3" class="has-text-grey has-text-centered">
            No tags yet. Upload a sound with tags to create some.
          </td>
        </tr>
      </tbody>
    </table>
    <p v-if="tags.error" class="has-text-danger">{{ tags.error }}</p>

    <ConfirmDialog
      v-if="deleting"
      title="Delete tag"
      :message="deleteMessage"
      @confirm="confirmDelete"
      @close="deleting = null"
    />

    <RenameDialog
      v-if="renaming"
      title="Rename tag"
      label="Tag name"
      :initial="renaming.name"
      :maxlength="32"
      placeholder="lowercase, a-z 0-9 _-"
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
import { useTagsStore } from "@/stores/tags";
import type { TagOut } from "@/api";

const tags = useTagsStore();
const deleting = ref<TagOut | null>(null);
const renaming = ref<TagOut | null>(null);
const renameError = ref<string | null>(null);
const renameLoading = ref(false);

const deleteMessage = computed(() => {
  const t = deleting.value;
  if (!t) return "";
  const suffix = t.sound_count > 0
    ? ` It is used by ${t.sound_count} sound${t.sound_count === 1 ? "" : "s"}.`
    : "";
  return `Delete tag '${t.name}'?${suffix}`;
});

onMounted(() => {
  void tags.refresh();
});

async function confirmDelete(): Promise<void> {
  const t = deleting.value;
  if (!t) return;
  await tags.remove(t.id);
}

function openRename(t: TagOut): void {
  renaming.value = t;
  renameError.value = null;
}

function closeRename(): void {
  renaming.value = null;
  renameError.value = null;
  renameLoading.value = false;
}

async function confirmRename(newName: string): Promise<void> {
  const t = renaming.value;
  if (!t) return;
  renameLoading.value = true;
  const ok = await tags.rename(t.id, newName);
  renameLoading.value = false;
  if (ok) closeRename();
  else renameError.value = tags.error;
}
</script>

<style scoped>
.header-row {
  display: flex;
  align-items: baseline;
  margin-bottom: 0.25rem;
}
</style>
