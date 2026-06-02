import { defineStore } from "pinia";
import { ref } from "vue";

import { api } from "@/api";
import type { ExploreResult } from "@/api";

export const useExploreStore = defineStore("explore", () => {
  const query = ref("");
  const page = ref(1);
  const results = ref<ExploreResult[]>([]);
  const hasMore = ref(false);
  const loading = ref(false);
  const error = ref<string | null>(null);

  function reset(): void {
    query.value = "";
    page.value = 1;
    results.value = [];
    hasMore.value = false;
    error.value = null;
  }

  async function _fetch(q: string, p: number, append: boolean): Promise<void> {
    loading.value = true;
    error.value = null;
    const { data, response } = await api.GET("/api/explore/search", {
      params: { query: { q, page: p } },
    });
    if (data) {
      results.value = append ? [...results.value, ...data.results] : data.results;
      hasMore.value = data.has_more;
      page.value = p;
      query.value = q;
    } else if (response.status === 502 || response.status === 504) {
      error.value = "Myinstants is not reachable right now.";
      if (!append) {
        results.value = [];
        hasMore.value = false;
      }
    } else {
      error.value = "Search failed.";
      if (!append) {
        results.value = [];
        hasMore.value = false;
      }
    }
    loading.value = false;
  }

  async function search(q: string): Promise<void> {
    results.value = [];
    hasMore.value = false;
    page.value = 1;
    await _fetch(q, 1, false);
  }

  async function loadMore(): Promise<void> {
    if (loading.value || !hasMore.value) return;
    await _fetch(query.value, page.value + 1, true);
  }

  return { query, page, results, hasMore, loading, error, search, loadMore, reset };
});
