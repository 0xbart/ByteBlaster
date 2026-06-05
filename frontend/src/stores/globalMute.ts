import { defineStore } from "pinia";
import { ref } from "vue";

import { api } from "@/api";

export const useGlobalMuteStore = defineStore("globalMute", () => {
  const active = ref(false);
  const by = ref<string | null>(null);
  const at = ref<string | null>(null);
  const error = ref<string | null>(null);

  async function refresh(): Promise<void> {
    const { data } = await api.GET("/api/global-mute");
    if (data) {
      active.value = data.active;
      by.value = data.by ?? null;
      at.value = data.at ?? null;
    }
  }

  async function setActive(value: boolean): Promise<boolean> {
    const { data, response } = await api.POST("/api/global-mute", {
      body: { active: value },
    });
    if (data) {
      active.value = data.active;
      by.value = data.by ?? null;
      at.value = data.at ?? null;
      error.value = null;
      return true;
    }
    error.value = response.status === 403 ? "Mutemaster privileges required." : "Toggle failed.";
    return false;
  }

  function applyEvent(ev: { active: boolean; by: string | null; at?: string | null }): void {
    active.value = ev.active;
    by.value = ev.by ?? null;
    at.value = ev.at ?? null;
  }

  return { active, by, at, error, refresh, setActive, applyEvent };
});
