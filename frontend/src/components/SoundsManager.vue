<template>
  <div>
    <h3 class="title is-5">Sounds</h3>
    <b-input
      v-model="filter"
      placeholder="Search by name, uploader, or tag"
      icon="magnifying-glass"
      clearable
      class="mb-3"
    />
    <table class="table is-fullwidth is-striped is-hoverable">
      <thead>
        <tr>
          <th>Name</th>
          <th>Uploader</th>
          <th>Tags</th>
          <th class="has-text-right">Actions</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="s in filtered" :key="s.id">
          <td>
            {{ s.display_name }}
            <span v-if="s.category_name" class="tag is-info is-light ml-2">
              {{ s.category_name }}
            </span>
          </td>
          <td>{{ s.uploader_username }}</td>
          <td>
            <b-taglist v-if="s.tags.length">
              <b-tag v-for="t in s.tags" :key="t" type="is-light">#{{ t }}</b-tag>
            </b-taglist>
            <span v-else class="has-text-grey-light">—</span>
          </td>
          <td class="has-text-right">
            <b-button
              size="is-small"
              type="is-info"
              icon-left="pencil"
              class="mr-2"
              @click="editing = s"
            >
              Edit
            </b-button>
            <b-button
              size="is-small"
              type="is-danger"
              icon-left="trash"
              @click="deleting = s"
            >
              Delete
            </b-button>
          </td>
        </tr>
        <tr v-if="!filtered.length">
          <td colspan="4" class="has-text-centered has-text-grey py-4">
            No sounds match.
          </td>
        </tr>
      </tbody>
    </table>

    <EditSoundDialog v-if="editing" :sound="editing" @close="editing = null" />
    <ConfirmDialog
      v-if="deleting"
      title="Delete sound"
      :message="`Delete '${deleting.display_name}'? This cannot be undone.`"
      @confirm="confirmDelete"
      @close="deleting = null"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import EditSoundDialog from "./EditSoundDialog.vue";
import ConfirmDialog from "./ConfirmDialog.vue";
import { useSoundsStore } from "@/stores/sounds";
import type { SoundOut } from "@/api";

const sounds = useSoundsStore();
const filter = ref("");
const editing = ref<SoundOut | null>(null);
const deleting = ref<SoundOut | null>(null);

onMounted(() => {
  if (!sounds.sounds.length) void sounds.refresh();
});

const filtered = computed<SoundOut[]>(() => {
  const f = filter.value.trim().toLowerCase();
  const list = sounds.sortedByName;
  if (!f) return list;
  return list.filter(
    (s) =>
      s.display_name.toLowerCase().includes(f) ||
      s.uploader_username.toLowerCase().includes(f) ||
      s.tags.some((t) => t.toLowerCase().includes(f)) ||
      (s.category_name?.toLowerCase().includes(f) ?? false),
  );
});

async function confirmDelete(): Promise<void> {
  const s = deleting.value;
  if (!s) return;
  await sounds.remove(s.id);
}
</script>
