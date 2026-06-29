import { defineStore } from "pinia";
import { ref } from "vue";

import { api } from "@/api";
import type { CategoryOut } from "@/api";

const LAST_CATEGORY_KEY = "lastCategoryId";

function loadLastCategoryId(): number | null {
  const raw = localStorage.getItem(LAST_CATEGORY_KEY);
  if (raw == null) return null;
  const n = Number(raw);
  return Number.isFinite(n) ? n : null;
}

export const useCategoriesStore = defineStore("categories", () => {
  const categories = ref<CategoryOut[]>([]);
  const error = ref<string | null>(null);
  const lastCategoryId = ref<number | null>(loadLastCategoryId());

  function rememberCategory(id: number | null): void {
    lastCategoryId.value = id;
    if (id == null) localStorage.removeItem(LAST_CATEGORY_KEY);
    else localStorage.setItem(LAST_CATEGORY_KEY, String(id));
  }

  async function refresh(): Promise<void> {
    const { data } = await api.GET("/api/categories");
    if (data) {
      categories.value = data;
      error.value = null;
    }
  }

  async function create(name: string): Promise<boolean> {
    const { data, response } = await api.POST("/api/categories", { body: { name } });
    if (data) {
      categories.value = [...categories.value, data].sort((a, b) =>
        a.name.localeCompare(b.name)
      );
      return true;
    }
    error.value = response.status === 409 ? "Name already exists." : "Create failed.";
    return false;
  }

  async function rename(id: number, name: string): Promise<boolean> {
    const { data, response } = await api.PATCH("/api/categories/{category_id}", {
      params: { path: { category_id: id } },
      body: { name },
    });
    if (data) {
      const idx = categories.value.findIndex((c) => c.id === id);
      if (idx >= 0) categories.value[idx] = data;
      categories.value.sort((a, b) => a.name.localeCompare(b.name));
      error.value = null;
      return true;
    }
    error.value = response.status === 409 ? "Name already exists." : "Rename failed.";
    return false;
  }

  function applyRename(id: number, newName: string): void {
    const idx = categories.value.findIndex((c) => c.id === id);
    if (idx >= 0) {
      categories.value[idx] = { ...categories.value[idx], name: newName };
      categories.value.sort((a, b) => a.name.localeCompare(b.name));
    }
  }

  async function remove(id: number): Promise<boolean> {
    const { response } = await api.DELETE("/api/categories/{category_id}", {
      params: { path: { category_id: id } },
    });
    if (response.status === 204) {
      categories.value = categories.value.filter((c) => c.id !== id);
      if (lastCategoryId.value === id) rememberCategory(null);
      return true;
    }
    error.value = "Delete failed.";
    return false;
  }

  return {
    categories,
    error,
    lastCategoryId,
    rememberCategory,
    refresh,
    create,
    rename,
    remove,
    applyRename,
  };
});
