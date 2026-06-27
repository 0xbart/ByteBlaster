import { defineStore } from "pinia";
import { ref } from "vue";

import { api } from "@/api";
import type { PlayOut } from "@/api";

const MAX_ITEMS = 50;

export type FeedItem =
  | { kind: "play"; key: string; playId: number; soundId: number; username: string; soundName: string; at: string }
  | { kind: "join"; key: string; username: string; at: string }
  | { kind: "leave"; key: string; username: string; at: string }
  | { kind: "sound_added"; key: string; username: string; soundName: string; at: string }
  | { kind: "sound_updated"; key: string; username: string; soundName: string; at: string }
  | { kind: "sound_removed"; key: string; username: string; soundName: string; at: string }
  | { kind: "mute_on"; key: string; username: string; at: string }
  | { kind: "mute_off"; key: string; username: string | null; at: string }
  | { kind: "ban_on"; key: string; username: string; by: string; at: string }
  | { kind: "ban_off"; key: string; username: string; by: string; at: string };

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
        playId: p.id,
        soundId: p.sound_id,
        username: p.played_by_username,
        soundName: p.sound_display_name,
        at: p.played_at,
      }));
    }
  }

  function prependPlay(entry: PlayOut): void {
    items.value = [
      {
        kind: "play" as const,
        key: `play-${entry.id}-${Date.now()}`,
        playId: entry.id,
        soundId: entry.sound_id,
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
        kind: "join" as const,
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
        kind: "leave" as const,
        key: `leave-${username}-${Date.now()}`,
        username,
        at: new Date().toISOString(),
      },
      ...items.value,
    ].slice(0, MAX_ITEMS);
  }

  function prependSoundEvent(
    kind: "sound_added" | "sound_updated" | "sound_removed",
    username: string,
    soundName: string,
  ): void {
    items.value = [
      {
        kind,
        key: `${kind}-${username}-${soundName}-${Date.now()}`,
        username,
        soundName,
        at: new Date().toISOString(),
      } as FeedItem,
      ...items.value,
    ].slice(0, MAX_ITEMS);
  }

  function prependMuteOn(username: string): void {
    items.value = [
      {
        kind: "mute_on" as const,
        key: `mute-on-${username}-${Date.now()}`,
        username,
        at: new Date().toISOString(),
      },
      ...items.value,
    ].slice(0, MAX_ITEMS);
  }

  function prependMuteOff(username: string | null): void {
    items.value = [
      {
        kind: "mute_off" as const,
        key: `mute-off-${username ?? "auto"}-${Date.now()}`,
        username,
        at: new Date().toISOString(),
      },
      ...items.value,
    ].slice(0, MAX_ITEMS);
  }

  function prependBan(username: string, active: boolean, by: string): void {
    items.value = [
      {
        kind: active ? ("ban_on" as const) : ("ban_off" as const),
        key: `ban-${active ? "on" : "off"}-${username}-${Date.now()}`,
        username,
        by,
        at: new Date().toISOString(),
      },
      ...items.value,
    ].slice(0, MAX_ITEMS);
  }

  function prependSoundAdded(username: string, soundName: string): void {
    prependSoundEvent("sound_added", username, soundName);
  }
  function prependSoundUpdated(username: string, soundName: string): void {
    prependSoundEvent("sound_updated", username, soundName);
  }
  function prependSoundRemoved(username: string, soundName: string): void {
    prependSoundEvent("sound_removed", username, soundName);
  }

  return {
    items,
    refresh,
    prependPlay,
    prependJoin,
    prependLeave,
    prependSoundAdded,
    prependSoundUpdated,
    prependSoundRemoved,
    prependMuteOn,
    prependMuteOff,
    prependBan,
  };
});
