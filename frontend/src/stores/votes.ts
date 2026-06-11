import { defineStore } from "pinia";
import { ref } from "vue";

import { useWsStore } from "@/stores/ws";
import { useUserStore } from "@/stores/user";

// Ephemeral thumbs up/down reactions on recent plays. State mirrors the
// backend's short-lived voting window; nothing is persisted.
export type VoteDirection = "up" | "down";

export interface VoteVoter {
  username: string;
  direction: VoteDirection;
}

export interface VoteTally {
  up: number;
  down: number;
  voters: VoteVoter[];
}

export interface VoteEvent {
  type: "vote";
  play_id: number;
  by: string;
  direction: VoteDirection;
  up: number;
  down: number;
  voters: VoteVoter[];
  at: string;
}

interface Popup {
  playId: number;
  name: string;
  expiresAt: number;
  myVote: VoteDirection | null;
}

const POPUP_MS = 20_000;
const MAX_TALLIES = 100;

export const useVotesStore = defineStore("votes", () => {
  const ws = useWsStore();
  const user = useUserStore();

  // Only the latest play gets a popup; a new play replaces it.
  const popup = ref<Popup | null>(null);
  const tallies = ref<Record<number, VoteTally>>({});
  let timer: number | null = null;

  function close(): void {
    popup.value = null;
    if (timer !== null) {
      window.clearTimeout(timer);
      timer = null;
    }
  }

  function openPopup(playId: number, name: string): void {
    if (timer !== null) window.clearTimeout(timer);
    popup.value = { playId, name, expiresAt: Date.now() + POPUP_MS, myVote: null };
    timer = window.setTimeout(close, POPUP_MS);
  }

  function vote(direction: VoteDirection): void {
    const p = popup.value;
    if (!p) return;
    // Optimistic toggle for button highlight; backend echo reconciles.
    p.myVote = p.myVote === direction ? null : direction;
    ws.sendVote(p.playId, direction);
  }

  function applyVote(ev: VoteEvent): void {
    const next = { ...tallies.value, [ev.play_id]: { up: ev.up, down: ev.down, voters: ev.voters } };
    // Bound the map: drop oldest inserted entries.
    const keys = Object.keys(next);
    if (keys.length > MAX_TALLIES) {
      for (const k of keys.slice(0, keys.length - MAX_TALLIES)) delete next[Number(k)];
    }
    tallies.value = next;

    // Reconcile our own highlight from the authoritative voter list.
    const p = popup.value;
    if (p && p.playId === ev.play_id) {
      const mine = ev.voters.find((v) => v.username === user.me?.username);
      p.myVote = mine?.direction ?? null;
    }
  }

  function tally(playId: number): VoteTally | null {
    return tallies.value[playId] ?? null;
  }

  return { popup, tallies, openPopup, close, vote, applyVote, tally };
});
