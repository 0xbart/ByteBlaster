import { defineStore } from "pinia";
import { ref } from "vue";

import { api } from "@/api";
import type { UserOut } from "@/api";

export const useAdminStore = defineStore("admin", () => {
  const users = ref<UserOut[]>([]);
  const error = ref<string | null>(null);

  async function refreshUsers(): Promise<void> {
    const { data, response } = await api.GET("/api/users");
    if (data) {
      users.value = data;
      error.value = null;
    } else if (response.status === 403) {
      error.value = "Admin privileges required.";
    }
  }

  async function setAdmin(id: number, isAdmin: boolean): Promise<boolean> {
    const { data, response } = await api.PATCH("/api/users/{user_id}", {
      params: { path: { user_id: id } },
      body: { is_admin: isAdmin },
    });
    if (data) {
      const idx = users.value.findIndex((u) => u.id === id);
      if (idx >= 0) users.value[idx] = data;
      return true;
    }
    error.value = response.status === 403 ? "Superadmin cannot be modified." : "Failed.";
    return false;
  }

  async function setMutemaster(id: number, value: boolean): Promise<boolean> {
    const { data, response } = await api.PATCH("/api/users/{user_id}", {
      params: { path: { user_id: id } },
      body: { is_mutemaster: value },
    });
    if (data) {
      const idx = users.value.findIndex((u) => u.id === id);
      if (idx >= 0) users.value[idx] = data;
      return true;
    }
    error.value = response.status === 403 ? "Only the superadmin can grant mutemaster." : "Failed.";
    return false;
  }

  async function removeUser(id: number): Promise<boolean> {
    const { response } = await api.DELETE("/api/users/{user_id}", {
      params: { path: { user_id: id } },
    });
    if (response.status === 204) {
      users.value = users.value.filter((u) => u.id !== id);
      return true;
    }
    error.value = response.status === 403 ? "Superadmin cannot be deleted." : "Failed.";
    return false;
  }

  return { users, error, refreshUsers, setAdmin, setMutemaster, removeUser };
});
