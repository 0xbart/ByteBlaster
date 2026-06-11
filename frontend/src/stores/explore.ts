import { defineStore } from "pinia";
import { ref } from "vue";

import { api } from "@/api";
import type { ExploreResult, LocalCategory, YoutubeFetchOut } from "@/api";

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

  // --- YouTube tab ---
  const youtubeUrl = ref("");
  const youtubeResult = ref<YoutubeFetchOut | null>(null);
  const youtubeLoading = ref(false);
  const youtubeError = ref<string | null>(null);

  async function fetchYoutube(url: string): Promise<void> {
    youtubeUrl.value = url;
    youtubeResult.value = null;
    youtubeError.value = null;
    youtubeLoading.value = true;
    const { data, error, response } = await api.POST("/api/explore/youtube/fetch", {
      body: { url },
    });
    if (data) {
      youtubeResult.value = data;
    } else {
      let msg: string | null = null;
      const detail = (error as { detail?: unknown } | undefined)?.detail;
      if (typeof detail === "string") {
        msg = detail;
      } else if (Array.isArray(detail) && detail.length > 0) {
        const first = detail[0] as { msg?: string };
        msg = first.msg ?? null;
      }
      if (!msg) {
        if (response.status === 502 || response.status === 504) {
          msg = "YouTube is not reachable right now.";
        } else {
          msg = `Fetch failed (HTTP ${response.status}).`;
        }
      }
      youtubeError.value = msg;
    }
    youtubeLoading.value = false;
  }

  function resetYoutube(): void {
    youtubeUrl.value = "";
    youtubeResult.value = null;
    youtubeError.value = null;
  }

  // --- Local library tab ---
  const localCategories = ref<LocalCategory[]>([]);
  const localLoading = ref(false);
  const localLoaded = ref(false);
  const localError = ref<string | null>(null);

  async function loadLocal(): Promise<void> {
    localLoading.value = true;
    localError.value = null;
    const { data } = await api.GET("/api/explore/local");
    if (data) {
      localCategories.value = data.categories;
      localLoaded.value = true;
    } else {
      localError.value = "Failed to load local sounds.";
    }
    localLoading.value = false;
  }

  async function importLocal(
    rel: string,
    displayName: string,
    categoryId: number | null,
    tags: string[],
  ): Promise<boolean> {
    const { data } = await api.POST("/api/explore/local/import", {
      body: { rel, display_name: displayName, category_id: categoryId, tags },
    });
    // On success the backend broadcasts sound_added, so the soundboard updates
    // via the WS handler — nothing to do here besides report ok.
    return !!data;
  }

  return {
    query,
    page,
    results,
    hasMore,
    loading,
    error,
    search,
    loadMore,
    reset,
    youtubeUrl,
    youtubeResult,
    youtubeLoading,
    youtubeError,
    fetchYoutube,
    resetYoutube,
    localCategories,
    localLoading,
    localLoaded,
    localError,
    loadLocal,
    importLocal,
  };
});
