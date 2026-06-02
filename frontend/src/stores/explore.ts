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

  async function search(q: string, p = 1): Promise<void> {
    query.value = q;
    page.value = p;
    results.value = [];
    hasMore.value = false;
    error.value = null;
    loading.value = true;
    const { data, response } = await api.GET("/api/explore/search", {
      params: { query: { q, page: p } },
    });
    if (data) {
      results.value = data.results;
      hasMore.value = data.has_more;
    } else if (response.status === 502 || response.status === 504) {
      error.value = "Myinstants is not reachable right now.";
      results.value = [];
      hasMore.value = false;
    } else {
      error.value = "Search failed.";
      results.value = [];
      hasMore.value = false;
    }
    loading.value = false;
  }

  function nextPage(): void {
    if (!loading.value && hasMore.value) void search(query.value, page.value + 1);
  }
  function prevPage(): void {
    if (!loading.value && page.value > 1) void search(query.value, page.value - 1);
  }

  return { query, page, results, hasMore, loading, error, search, nextPage, prevPage, reset };
});
