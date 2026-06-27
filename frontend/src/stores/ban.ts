import { defineStore } from "pinia";
import { ref } from "vue";

import type { UserOut } from "@/api";

export const useBanStore = defineStore("ban", () => {
  const banned = ref(false);
  const expiresAt = ref<string | null>(null);
  const by = ref<string | null>(null);

  let expiryTimer: number | null = null;

  function clearTimer(): void {
    if (expiryTimer !== null) {
      window.clearTimeout(expiryTimer);
      expiryTimer = null;
    }
  }

  function lift(): void {
    banned.value = false;
    expiresAt.value = null;
    by.value = null;
    clearTimer();
  }

  /** Apply a ban (or lift it). Schedules a local auto-lift at `expires`. */
  function setBan(active: boolean, expires: string | null, actor: string | null): void {
    clearTimer();
    if (!active) {
      lift();
      return;
    }
    banned.value = true;
    expiresAt.value = expires;
    by.value = actor;
    if (expires) {
      const ms = new Date(expires).getTime() - Date.now();
      // Re-enable the UI when the timed ban elapses, even without a server event.
      expiryTimer = window.setTimeout(lift, Math.max(0, ms));
    }
  }

  /** Seed initial state from the current user (page load). */
  function initFrom(me: UserOut | null): void {
    if (me?.is_banned) {
      setBan(true, me.ban_expires_at ?? null, null);
    } else {
      lift();
    }
  }

  return { banned, expiresAt, by, setBan, initFrom };
});
