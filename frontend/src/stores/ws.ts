import { defineStore } from "pinia";
import { ref } from "vue";

// Bridges components to the single WebSocket owned by useWebSocket(). The
// composable registers its send function on mount; components send through here
// instead of opening their own socket.
export const useWsStore = defineStore("ws", () => {
  const sender = ref<((payload: unknown) => boolean) | null>(null);

  function register(fn: ((payload: unknown) => boolean) | null): void {
    sender.value = fn;
  }

  // Superadmin-only on the backend; pushes a theme override to one user.
  function setUserTheme(
    targetUserId: number,
    mode: "light" | "dark",
    skin: "default" | "cyber" | "pink",
  ): boolean {
    return (
      sender.value?.({
        type: "set_theme",
        target_user_id: targetUserId,
        mode,
        skin,
      }) ?? false
    );
  }

  return { register, setUserTheme };
});
