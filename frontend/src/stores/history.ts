import { defineStore } from "pinia";
import { ref } from "vue";

import { api } from "@/api";
import type { PlayOut } from "@/api";

const MAX_ITEMS = 50;

export const useHistoryStore = defineStore("history", () => {
  const plays = ref<PlayOut[]>([]);

  async function refresh(): Promise<void> {
    const { data } = await api.GET("/api/plays", {
      params: { query: { limit: MAX_ITEMS } },
    });
    if (data) plays.value = data;
  }

  function prepend(entry: PlayOut): void {
    plays.value = [entry, ...plays.value].slice(0, MAX_ITEMS);
  }

  return { plays, refresh, prepend };
});
