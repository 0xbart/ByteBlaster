import { defineStore } from "pinia";
import { ref } from "vue";

import { api } from "@/api";
import type { PlayOut } from "@/api";

const MAX_ITEMS = 50;

export type FeedItem =
  | { kind: "play"; key: string; username: string; soundName: string; at: string }
  | { kind: "join"; key: string; username: string; at: string }
  | { kind: "leave"; key: string; username: string; at: string };

export const useHistoryStore = defineStore("history", () => {
  const items = ref<FeedItem[]>([]);

  async function refresh(): Promise<void> {
    const { data } = await api.GET("/api/plays", {
      params: { query: { limit: MAX_ITEMS } },
    });
    if (data) {
      items.value = data.map((p: PlayOut) => ({
        kind: "play" as const,
        key: `play-${p.id}`,
        username: p.played_by_username,
        soundName: p.sound_display_name,
        at: p.played_at,
      }));
    }
  }

  function prependPlay(entry: PlayOut): void {
    items.value = [
      {
        kind: "play",
        key: `play-${entry.id}-${Date.now()}`,
        username: entry.played_by_username,
        soundName: entry.sound_display_name,
        at: entry.played_at,
      },
      ...items.value,
    ].slice(0, MAX_ITEMS);
  }

  function prependJoin(username: string): void {
    items.value = [
      {
        kind: "join",
        key: `join-${username}-${Date.now()}`,
        username,
        at: new Date().toISOString(),
      },
      ...items.value,
    ].slice(0, MAX_ITEMS);
  }

  function prependLeave(username: string): void {
    items.value = [
      {
        kind: "leave",
        key: `leave-${username}-${Date.now()}`,
        username,
        at: new Date().toISOString(),
      },
      ...items.value,
    ].slice(0, MAX_ITEMS);
  }

  return { items, refresh, prependPlay, prependJoin, prependLeave };
});
