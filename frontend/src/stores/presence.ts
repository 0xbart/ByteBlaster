import { defineStore } from "pinia";
import { computed, ref } from "vue";

export interface PresenceUser {
  id: number;
  username: string;
  ip: string;
  is_admin?: boolean;
  is_superadmin?: boolean;
  is_banned?: boolean;
  volume?: number;
}

export const usePresenceStore = defineStore("presence", () => {
  // Server is the source of truth: every WS connect/disconnect re-broadcasts
  // the full list, so we just overwrite on each event.
  const users = ref<PresenceUser[]>([]);
  const count = computed(() => users.value.length);

  function setUsers(list: PresenceUser[]): void {
    users.value = list;
  }

  function reset(): void {
    users.value = [];
  }

  return { users, count, setUsers, reset };
});
