import { defineStore } from "pinia";
import { ref } from "vue";

import { api } from "@/api";
import type { TagOut } from "@/api";

export const useTagsStore = defineStore("tags", () => {
  const tags = ref<TagOut[]>([]);
  const error = ref<string | null>(null);

  async function refresh(): Promise<void> {
    const { data } = await api.GET("/api/tags");
    if (data) {
      tags.value = data;
      error.value = null;
    }
  }

  function upsertNames(names: string[]): void {
    // Newly-created tags returned via WS-embedded SoundOut may not yet be in
    // our list; merge so autocomplete picks them up without a full refetch.
    const known = new Set(tags.value.map((t) => t.name));
    const missing = names.filter((n) => !known.has(n));
    if (!missing.length) return;
    const stub = missing.map((name) => ({
      id: -1,
      name,
      created_at: new Date().toISOString(),
      sound_count: 1,
    }));
    tags.value = [...tags.value, ...stub].sort((a, b) => a.name.localeCompare(b.name));
  }

  function removeLocal(name: string): void {
    tags.value = tags.value.filter((t) => t.name !== name);
  }

  async function rename(id: number, name: string): Promise<boolean> {
    const { data, response } = await api.PATCH("/api/tags/{tag_id}", {
      params: { path: { tag_id: id } },
      body: { name },
    });
    if (data) {
      const idx = tags.value.findIndex((t) => t.id === id);
      if (idx >= 0) tags.value[idx] = data;
      tags.value.sort((a, b) => a.name.localeCompare(b.name));
      error.value = null;
      return true;
    }
    if (response.status === 409) error.value = "Name already exists.";
    else if (response.status === 422) error.value = "Invalid tag (1–32 chars, a-z 0-9 _-).";
    else error.value = "Rename failed.";
    return false;
  }

  function applyRename(id: number, oldName: string, newName: string): void {
    const idx = tags.value.findIndex((t) => t.id === id);
    if (idx >= 0) {
      tags.value[idx] = { ...tags.value[idx], name: newName };
      tags.value.sort((a, b) => a.name.localeCompare(b.name));
    } else if (oldName) {
      const oldIdx = tags.value.findIndex((t) => t.name === oldName);
      if (oldIdx >= 0) {
        tags.value[oldIdx] = { ...tags.value[oldIdx], name: newName };
        tags.value.sort((a, b) => a.name.localeCompare(b.name));
      }
    }
  }

  async function remove(id: number): Promise<boolean> {
    const { response } = await api.DELETE("/api/tags/{tag_id}", {
      params: { path: { tag_id: id } },
    });
    if (response.status === 204) {
      tags.value = tags.value.filter((t) => t.id !== id);
      return true;
    }
    error.value = response.status === 403 ? "Admin privileges required." : "Delete failed.";
    return false;
  }

  return { tags, error, refresh, upsertNames, removeLocal, remove, rename, applyRename };
});
