import { defineStore } from "pinia";
import { ref, computed } from "vue";

import { api } from "@/api";
import type { UserOut } from "@/api";

export const useUserStore = defineStore("user", () => {
  const me = ref<UserOut | null>(null);
  const ip = ref<string>("");
  const loaded = ref(false);
  const claimError = ref<string | null>(null);

  const needsClaim = computed(() => loaded.value && me.value === null);
  const isReady = computed(() => loaded.value && me.value !== null);
  const isAdmin = computed(() => !!me.value?.is_admin);
  const isSuperadmin = computed(() => !!me.value?.is_superadmin);

  async function fetchMe(): Promise<void> {
    const { data } = await api.GET("/api/me");
    if (data) {
      me.value = data.user ?? null;
      ip.value = data.ip;
    }
    loaded.value = true;
  }

  async function claim(username: string): Promise<boolean> {
    claimError.value = null;
    const { data, response } = await api.POST("/api/me/claim", {
      body: { username },
    });
    if (data) {
      me.value = data;
      return true;
    }
    if (response.status === 409) {
      claimError.value = "Username or IP already taken.";
    } else {
      claimError.value = "Claim failed.";
    }
    return false;
  }

  return {
    me,
    ip,
    loaded,
    needsClaim,
    isReady,
    isAdmin,
    isSuperadmin,
    claimError,
    fetchMe,
    claim,
  };
});
