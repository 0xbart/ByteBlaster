import { defineStore } from "pinia";
import { ref } from "vue";

import { api } from "@/api";
import type { SoundStatOut, UserStatOut } from "@/api";

function sortSoundStats(list: SoundStatOut[]): void {
  list.sort(
    (a, b) =>
      b.play_count - a.play_count ||
      a.display_name.localeCompare(b.display_name),
  );
}

function sortUserStats(list: UserStatOut[]): void {
  list.sort(
    (a, b) =>
      b.play_count - a.play_count || a.username.localeCompare(b.username),
  );
}

export const useStatsStore = defineStore("stats", () => {
  const allTime = ref<SoundStatOut[]>([]);
  const trending = ref<SoundStatOut[]>([]);
  const users = ref<UserStatOut[]>([]);
  const loading = ref(false);

  async function refresh(): Promise<void> {
    loading.value = true;
    const [a, t, u] = await Promise.all([
      api.GET("/api/stats/sounds"),
      api.GET("/api/stats/trending", {
        params: { query: { days: 7, limit: 10 } },
      }),
      api.GET("/api/stats/users", { params: { query: { limit: 20 } } }),
    ]);
    if (a.data) allTime.value = a.data;
    if (t.data) trending.value = t.data;
    if (u.data) users.value = u.data;
    loading.value = false;
  }

  function bump(soundId: number, displayName: string, username: string): void {
    for (const list of [allTime.value, trending.value]) {
      const idx = list.findIndex((s) => s.sound_id === soundId);
      if (idx >= 0) list[idx].play_count++;
    }
    if (!trending.value.some((s) => s.sound_id === soundId)) {
      trending.value.push({
        sound_id: soundId,
        display_name: displayName,
        category_name: null,
        play_count: 1,
      });
    }
    const uIdx = users.value.findIndex((u) => u.username === username);
    if (uIdx >= 0) users.value[uIdx].play_count++;
    else users.value.push({ user_id: 0, username, play_count: 1 });

    sortSoundStats(allTime.value);
    sortSoundStats(trending.value);
    sortUserStats(users.value);
  }

  function removeSound(soundId: number): void {
    allTime.value = allTime.value.filter((s) => s.sound_id !== soundId);
    trending.value = trending.value.filter((s) => s.sound_id !== soundId);
  }

  return { allTime, trending, users, loading, refresh, bump, removeSound };
});
