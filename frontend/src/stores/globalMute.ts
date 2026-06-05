import { defineStore } from "pinia";
import { ref } from "vue";

import { api } from "@/api";

export const useGlobalMuteStore = defineStore("globalMute", () => {
  const active = ref(false);
  const by = ref<string | null>(null);
  const at = ref<string | null>(null);
  const expiresAt = ref<string | null>(null);
  const error = ref<string | null>(null);

  function apply(data: {
    active: boolean;
    by?: string | null;
    at?: string | null;
    expires_at?: string | null;
  }): void {
    active.value = data.active;
    by.value = data.by ?? null;
    at.value = data.at ?? null;
    expiresAt.value = data.expires_at ?? null;
  }

  async function refresh(): Promise<void> {
    const { data } = await api.GET("/api/global-mute");
    if (data) apply(data);
  }

  async function setActive(
    value: boolean,
    durationMinutes?: number | null,
  ): Promise<boolean> {
    const body = value
      ? { active: true, duration_minutes: durationMinutes ?? null }
      : { active: false };
    const { data, response } = await api.POST("/api/global-mute", { body });
    if (data) {
      apply(data);
      error.value = null;
      return true;
    }
    error.value = response.status === 403 ? "Mutemaster privileges required." : "Toggle failed.";
    return false;
  }

  function applyEvent(ev: {
    active: boolean;
    by: string | null;
    at?: string | null;
    expires_at?: string | null;
  }): void {
    apply(ev);
  }

  return { active, by, at, expiresAt, error, refresh, setActive, applyEvent };
});
