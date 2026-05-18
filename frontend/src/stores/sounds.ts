import { defineStore } from "pinia";
import { ref, computed } from "vue";

import { api } from "@/api";
import type { SoundOut } from "@/api";

export const useSoundsStore = defineStore("sounds", () => {
  const sounds = ref<SoundOut[]>([]);
  const loading = ref(false);
  const error = ref<string | null>(null);

  const sortedByName = computed(() =>
    [...sounds.value].sort((a, b) => a.display_name.localeCompare(b.display_name))
  );

  async function refresh(): Promise<void> {
    loading.value = true;
    const { data } = await api.GET("/api/sounds");
    loading.value = false;
    if (!data) {
      error.value = "Failed to load sounds.";
      return;
    }
    sounds.value = data;
    error.value = null;
  }

  async function upload(
    source: File | string,
    displayName: string,
    categoryId: number | null = null,
    tags: string[] = [],
  ): Promise<boolean> {
    // Multipart upload — openapi-fetch routes through our bodySerializer so the
    // call still goes via the typed client (single source of truth) while the
    // wire format is FormData. `source` can be a local File or a remote URL
    // string; the backend downloads URLs server-side.
    const { data, response } = await api.POST("/api/sounds", {
      body: {
        file: source as unknown as string,
        display_name: displayName,
        category_id: categoryId,
        tags,
      },
      bodySerializer: (body) => {
        const b = body as unknown as {
          file: File | string;
          display_name: string;
          category_id: number | null;
          tags: string[];
        };
        const fd = new FormData();
        if (typeof b.file === "string") fd.append("url", b.file);
        else fd.append("file", b.file);
        fd.append("display_name", b.display_name);
        if (b.category_id != null) fd.append("category_id", String(b.category_id));
        for (const t of b.tags) fd.append("tags", t);
        return fd;
      },
    });
    if (!data) {
      if (response.status === 415) error.value = "File type not supported (mp3/wav only).";
      else if (response.status === 413) error.value = "File too large (max 10 MB).";
      else if (response.status === 422) error.value = "Invalid tag (1–32 chars, max 10).";
      else if (response.status === 400) {
        // Try to surface the backend's detail (URL fetch errors, bad URL, etc.).
        try {
          const body = (await response.clone().json()) as { detail?: string };
          error.value = body.detail ?? "Bad request.";
        } catch {
          error.value = "Bad request.";
        }
      }
      else error.value = "Upload failed.";
      return false;
    }
    upsert(data);
    return true;
  }

  async function update(
    id: number,
    patch: { display_name?: string; category_id?: number | null; tags?: string[] },
  ): Promise<boolean> {
    const { data, response } = await api.PATCH("/api/sounds/{sound_id}", {
      params: { path: { sound_id: id } },
      body: patch,
    });
    if (data) {
      upsert(data);
      return true;
    }
    if (response.status === 403) error.value = "Admin privileges required.";
    else if (response.status === 422) error.value = "Invalid tag (1–32 chars, max 10).";
    else error.value = "Update failed.";
    return false;
  }

  async function remove(id: number): Promise<boolean> {
    const { response } = await api.DELETE("/api/sounds/{sound_id}", {
      params: { path: { sound_id: id } },
    });
    if (response.status === 204) {
      sounds.value = sounds.value.filter((s) => s.id !== id);
      return true;
    }
    error.value = "Delete failed.";
    return false;
  }

  async function play(id: number): Promise<void> {
    // We deliberately do NOT play locally — wait for the WS broadcast so every
    // connected client (including ourselves) plays via the same codepath.
    await api.POST("/api/sounds/{sound_id}/play", {
      params: { path: { sound_id: id } },
    });
  }

  function upsert(sound: SoundOut): void {
    const idx = sounds.value.findIndex((s) => s.id === sound.id);
    if (idx >= 0) sounds.value[idx] = sound;
    else sounds.value.unshift(sound);
  }

  function removeLocal(id: number): void {
    sounds.value = sounds.value.filter((s) => s.id !== id);
  }

  function stripTag(name: string): void {
    // Strip a tag name from all cached sounds. Used when a tag is deleted
    // server-side (via WS broadcast) so chips disappear without a refetch.
    sounds.value = sounds.value.map((s) =>
      s.tags.includes(name) ? { ...s, tags: s.tags.filter((t) => t !== name) } : s,
    );
  }

  function renameTagLocal(oldName: string, newName: string): void {
    sounds.value = sounds.value.map((s) =>
      s.tags.includes(oldName)
        ? { ...s, tags: s.tags.map((t) => (t === oldName ? newName : t)) }
        : s,
    );
  }

  function renameCategoryLocal(categoryId: number, newName: string): void {
    sounds.value = sounds.value.map((s) =>
      s.category_id === categoryId ? { ...s, category_name: newName } : s,
    );
  }

  return {
    sounds,
    sortedByName,
    loading,
    error,
    refresh,
    upload,
    update,
    remove,
    play,
    upsert,
    removeLocal,
    stripTag,
    renameTagLocal,
    renameCategoryLocal,
  };
});
