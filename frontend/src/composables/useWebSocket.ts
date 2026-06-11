import { onBeforeUnmount, onMounted, ref, watch } from "vue";

import { useSoundsStore } from "@/stores/sounds";
import { useHistoryStore } from "@/stores/history";
import { useTagsStore } from "@/stores/tags";
import { useCategoriesStore } from "@/stores/categories";
import { useStatsStore } from "@/stores/stats";
import { useAudioStore } from "@/stores/audio";
import { useGlobalMuteStore } from "@/stores/globalMute";
import { usePartyStore } from "@/stores/party";
import { celebrate } from "./useConfetti";
import { usePresenceStore, type PresenceUser } from "@/stores/presence";
import { useThemeStore } from "@/stores/theme";
import { useWsStore } from "@/stores/ws";
import { useVotesStore, type VoteVoter } from "@/stores/votes";
import { floatVote } from "./useVoteGlyph";
import { useAudioPlayer } from "./useAudioPlayer";
import type { PlayOut, SoundOut } from "@/api";

type WsEvent =
  | { type: "play"; play_id: number; sound_id: number; sound_url: string; display_name: string; by: string; at: string }
  | { type: "vote"; play_id: number; by: string; direction: "up" | "down"; up: number; down: number; voters: VoteVoter[]; at: string }
  | { type: "sound_added"; sound: SoundOut; by: string }
  | { type: "sound_updated"; sound: SoundOut; by: string }
  | { type: "sound_removed"; sound_id: number; display_name: string; by: string }
  | { type: "tag_removed"; name: string }
  | { type: "tag_renamed"; id: number; old_name: string; new_name: string }
  | { type: "category_renamed"; id: number; new_name: string }
  | { type: "presence"; users: PresenceUser[] }
  | { type: "global_mute"; active: boolean; by: string | null; at: string | null; expires_at: string | null }
  | { type: "stop_all"; by: string }
  | { type: "theme_set"; mode: "light" | "dark"; skin: "default" | "cyber" | "pink"; by: string };

function wsUrl(): string {
  const proto = window.location.protocol === "https:" ? "wss:" : "ws:";
  return `${proto}//${window.location.host}/ws`;
}

export function useWebSocket() {
  const sounds = useSoundsStore();
  const history = useHistoryStore();
  const tags = useTagsStore();
  const categories = useCategoriesStore();
  const stats = useStatsStore();
  const audioStore = useAudioStore();
  const globalMute = useGlobalMuteStore();
  const party = usePartyStore();
  const presence = usePresenceStore();
  const theme = useThemeStore();
  const wsStore = useWsStore();
  const votes = useVotesStore();
  const audio = useAudioPlayer();

  const connected = ref(false);
  let socket: WebSocket | null = null;
  let reconnectTimer: number | null = null;
  let stopped = false;
  let prevSnapshotSeen = false;
  // Suppress repeated join/leave notices for the same user (e.g. rapid F5).
  const PRESENCE_COOLDOWN_MS = 10_000;
  const lastJoinAt = new Map<number, number>();
  const lastLeaveAt = new Map<number, number>();

  function dispatch(ev: WsEvent): void {
    switch (ev.type) {
      case "play":
        audio.play(ev.sound_url);
        // The full PlayOut isn't sent over WS to keep payload small; build a
        // shim entry for the history panel. The next /plays refresh re-syncs.
        history.prependPlay({
          id: ev.play_id,
          sound_id: ev.sound_id,
          sound_display_name: ev.display_name,
          played_by_user_id: 0,
          played_by_username: ev.by,
          played_at: ev.at,
        } satisfies PlayOut);
        stats.bump(ev.sound_id, ev.display_name, ev.by);
        votes.openPopup(ev.play_id, ev.display_name);
        if (party.active) celebrate();
        break;
      case "vote":
        votes.applyVote(ev);
        floatVote(ev.direction, ev.by);
        break;
      case "sound_added":
        sounds.upsert(ev.sound);
        history.prependSoundAdded(ev.by, ev.sound.display_name);
        break;
      case "sound_updated":
        sounds.upsert(ev.sound);
        history.prependSoundUpdated(ev.by, ev.sound.display_name);
        break;
      case "sound_removed":
        sounds.removeLocal(ev.sound_id);
        stats.removeSound(ev.sound_id);
        history.prependSoundRemoved(ev.by, ev.display_name);
        break;
      case "tag_removed":
        sounds.stripTag(ev.name);
        tags.removeLocal(ev.name);
        break;
      case "tag_renamed":
        sounds.renameTagLocal(ev.old_name, ev.new_name);
        tags.applyRename(ev.id, ev.old_name, ev.new_name);
        break;
      case "category_renamed":
        sounds.renameCategoryLocal(ev.id, ev.new_name);
        categories.applyRename(ev.id, ev.new_name);
        break;
      case "stop_all":
        audio.stopAll();
        break;
      case "theme_set":
        // A superadmin changed our theme remotely; apply immediately.
        theme.setMode(ev.mode);
        theme.setSkin(ev.skin);
        break;
      case "global_mute": {
        const wasActive = globalMute.active;
        globalMute.applyEvent(ev);
        if (ev.active) {
          audio.stopAll();
          if (!wasActive) history.prependMuteOn(ev.by ?? "someone");
        } else if (wasActive) {
          history.prependMuteOff(ev.by);
          celebrate();
        }
        break;
      }
      case "presence": {
        // Detect newly-joined users by diffing against the previous list.
        // Skip the very first presence snapshot (initial connect) to avoid
        // spamming "came online" for everyone already present.
        const prevUsers = presence.users;
        const prevIds = new Set(prevUsers.map((u) => u.id));
        const nextIds = new Set(ev.users.map((u) => u.id));
        if (prevSnapshotSeen) {
          const now = Date.now();
          // Joined: in new list, not in previous.
          for (const u of ev.users) {
            if (prevIds.has(u.id)) continue;
            if (now - (lastJoinAt.get(u.id) ?? 0) < PRESENCE_COOLDOWN_MS) continue;
            lastJoinAt.set(u.id, now);
            history.prependJoin(u.username);
          }
          // Left: in previous list, not in new.
          for (const u of prevUsers) {
            if (nextIds.has(u.id)) continue;
            if (now - (lastLeaveAt.get(u.id) ?? 0) < PRESENCE_COOLDOWN_MS) continue;
            lastLeaveAt.set(u.id, now);
            history.prependLeave(u.username);
          }
        }
        prevSnapshotSeen = true;
        presence.setUsers(ev.users);
        break;
      }
    }
  }

  function connect(): void {
    if (stopped) return;
    socket = new WebSocket(wsUrl());
    socket.onopen = () => {
      connected.value = true;
      sendVolume();
    };
    socket.onmessage = (msg) => {
      try {
        dispatch(JSON.parse(msg.data) as WsEvent);
      } catch (err) {
        // eslint-disable-next-line no-console
        console.warn("Bad WS payload", err);
      }
    };
    socket.onclose = () => {
      connected.value = false;
      // Avoid showing a stale online count while we're offline; the server
      // will re-send a fresh presence on reconnect anyway.
      presence.reset();
      // Treat the next presence snapshot as a fresh baseline (no join spam).
      prevSnapshotSeen = false;
      if (!stopped) reconnectTimer = window.setTimeout(connect, 2000);
    };
    socket.onerror = () => {
      socket?.close();
    };
  }

  function send(payload: unknown): boolean {
    if (socket?.readyState !== WebSocket.OPEN) return false;
    try {
      socket.send(JSON.stringify(payload));
      return true;
    } catch {
      return false;
    }
  }

  function sendVolume(): void {
    if (socket?.readyState !== WebSocket.OPEN) return;
    try {
      socket.send(JSON.stringify({ type: "volume", value: audioStore.volume }));
    } catch {
      // ignore
    }
  }

  let lastSent = audioStore.volume;
  let volumeDebounce: number | null = null;
  watch(
    () => audioStore.volume,
    (v) => {
      if (v === lastSent) return;
      if (volumeDebounce !== null) window.clearTimeout(volumeDebounce);
      volumeDebounce = window.setTimeout(() => {
        lastSent = v;
        sendVolume();
      }, 150);
    },
  );

  onMounted(() => {
    wsStore.register(send);
    connect();
  });
  onBeforeUnmount(() => {
    stopped = true;
    wsStore.register(null);
    if (reconnectTimer !== null) window.clearTimeout(reconnectTimer);
    if (volumeDebounce !== null) window.clearTimeout(volumeDebounce);
    socket?.close();
  });

  return { connected };
}
