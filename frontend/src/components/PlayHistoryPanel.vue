<template>
  <aside class="history-panel">
    <h2 class="title is-5">Recent activities</h2>
    <div class="scroll-area">
      <ul v-if="history.items.length" class="history-list">
        <li v-for="it in history.items" :key="it.key">
          <template v-if="it.kind === 'play'">
            <b-icon
              icon="circle-play"
              pack="fas"
              size="is-small"
              class="play-icon play-icon--clickable"
              @click="sounds.play(it.soundId)"
            />
            <strong class="play-user" :title="it.username">{{ clipName(it.username) }}</strong>
            <em class="play-name" :title="it.soundName">{{ it.soundName }}</em>
            <span
              v-if="voteTally(it.playId)"
              class="vote-tally is-size-7"
              :title="voterTitle(it.playId)"
            >
              <span v-if="voteTally(it.playId)!.up" class="vote-tally__up">👍{{ voteTally(it.playId)!.up }}</span>
              <span v-if="voteTally(it.playId)!.down" class="vote-tally__down">👎{{ voteTally(it.playId)!.down }}</span>
            </span>
            <span class="play-time has-text-grey is-size-7">{{ relativeTime(it.at) }}</span>
          </template>
          <template v-else-if="it.kind === 'join'">
            <b-icon icon="link" pack="fas" size="is-small" class="play-icon" />
            <strong class="play-user" :title="it.username">{{ clipName(it.username) }}</strong>
            <em class="play-name has-text-grey">came online</em>
            <span class="play-time has-text-grey is-size-7">{{ relativeTime(it.at) }}</span>
          </template>
          <template v-else-if="it.kind === 'leave'">
            <b-icon icon="link-slash" pack="fas" size="is-small" class="play-icon" />
            <strong class="play-user" :title="it.username">{{ clipName(it.username) }}</strong>
            <em class="play-name has-text-grey">went offline</em>
            <span class="play-time has-text-grey is-size-7">{{ relativeTime(it.at) }}</span>
          </template>
          <template v-else-if="it.kind === 'sound_added'">
            <b-icon icon="circle-plus" pack="fas" size="is-small" class="play-icon" />
            <strong class="play-user" :title="it.username">{{ clipName(it.username) }}</strong>
            <em class="play-name" :title="`added ${it.soundName}`">added {{ it.soundName }}</em>
            <span class="play-time has-text-grey is-size-7">{{ relativeTime(it.at) }}</span>
          </template>
          <template v-else-if="it.kind === 'sound_updated'">
            <b-icon icon="pencil" pack="fas" size="is-small" class="play-icon" />
            <strong class="play-user" :title="it.username">{{ clipName(it.username) }}</strong>
            <em class="play-name" :title="`edited ${it.soundName}`">edited {{ it.soundName }}</em>
            <span class="play-time has-text-grey is-size-7">{{ relativeTime(it.at) }}</span>
          </template>
          <template v-else-if="it.kind === 'sound_removed'">
            <b-icon icon="trash" pack="fas" size="is-small" class="play-icon" />
            <strong class="play-user" :title="it.username">{{ clipName(it.username) }}</strong>
            <em class="play-name" :title="`deleted ${it.soundName}`">deleted {{ it.soundName }}</em>
            <span class="play-time has-text-grey is-size-7">{{ relativeTime(it.at) }}</span>
          </template>
          <template v-else-if="it.kind === 'mute_on'">
            <b-icon icon="gavel" pack="fas" size="is-small" class="play-icon" />
            <strong class="play-user" :title="it.username">{{ clipName(it.username) }}</strong>
            <em class="play-name">muted everyone</em>
            <span class="play-time has-text-grey is-size-7">{{ relativeTime(it.at) }}</span>
          </template>
          <template v-else-if="it.kind === 'ban_on'">
            <b-icon icon="ban" pack="fas" size="is-small" class="play-icon has-text-danger" />
            <strong class="play-user" :title="it.username">{{ clipName(it.username) }}</strong>
            <em class="play-name" :title="`banned (${banDuration(it.durationMinutes)}) by ${it.by}`">banned ({{ banDuration(it.durationMinutes) }}) by {{ it.by }}</em>
            <span class="play-time has-text-grey is-size-7">{{ relativeTime(it.at) }}</span>
          </template>
          <template v-else-if="it.kind === 'ban_off'">
            <b-icon icon="user-check" pack="fas" size="is-small" class="play-icon" />
            <template v-if="it.by">
              <strong class="play-user" :title="it.username">{{ clipName(it.username) }}</strong>
              <em class="play-name" :title="`unbanned by ${it.by}`">unbanned by {{ it.by }}</em>
            </template>
            <em v-else class="play-name" :title="`Ban ${it.username} expired`">Ban {{ clipName(it.username) }} expired</em>
            <span class="play-time has-text-grey is-size-7">{{ relativeTime(it.at) }}</span>
          </template>
          <template v-else>
            <b-icon icon="volume-high" pack="fas" size="is-small" class="play-icon" />
            <strong class="play-user" :title="it.username ?? 'auto'">{{ clipName(it.username) }}</strong>
            <em class="play-name">lifted mute</em>
            <span class="play-time has-text-grey is-size-7">{{ relativeTime(it.at) }}</span>
          </template>
        </li>
      </ul>
      <p v-else class="has-text-grey">No plays yet.</p>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { onMounted, onBeforeUnmount, ref } from "vue";
import { useHistoryStore } from "@/stores/history";
import { useSoundsStore } from "@/stores/sounds";
import { useVotesStore, type VoteTally } from "@/stores/votes";

const history = useHistoryStore();
const sounds = useSoundsStore();
const votes = useVotesStore();

function banDuration(mins: number | null | undefined): string {
  if (mins == null || !Number.isFinite(mins) || mins <= 0) return "permanently";
  if (mins < 60) return `${mins} min`;
  const hours = Math.round(mins / 60);
  if (hours < 24) return `${hours} ${hours === 1 ? "hour" : "hours"}`;
  const days = Math.round(hours / 24);
  return `${days} ${days === 1 ? "day" : "days"}`;
}

function clipName(name: string | null | undefined): string {
  const n = name ?? "auto";
  return n.length > 17 ? `${n.slice(0, 17)}…` : n;
}

function voteTally(playId: number): VoteTally | null {
  return votes.tally(playId);
}

function voterTitle(playId: number): string {
  const t = votes.tally(playId);
  if (!t) return "";
  const up = t.voters.filter((v) => v.direction === "up").map((v) => v.username);
  const down = t.voters.filter((v) => v.direction === "down").map((v) => v.username);
  const parts: string[] = [];
  if (up.length) parts.push(`👍 ${up.join(", ")}`);
  if (down.length) parts.push(`👎 ${down.join(", ")}`);
  return parts.join("  ·  ");
}
const now = ref(Date.now());
let ticker: number | null = null;

onMounted(() => {
  void history.refresh();
  ticker = window.setInterval(() => {
    now.value = Date.now();
  }, 15_000);
});

onBeforeUnmount(() => {
  if (ticker !== null) window.clearInterval(ticker);
});

function relativeTime(iso: string): string {
  const t = new Date(iso).getTime();
  const s = Math.max(0, Math.floor((now.value - t) / 1000));
  if (s < 60) return `${s}s ago`;
  if (s < 3600) return `${Math.floor(s / 60)}m ago`;
  if (s < 86400) return `${Math.floor(s / 3600)}h ago`;
  return new Date(iso).toLocaleString();
}
</script>

<style scoped>
.history-panel {
  background: var(--bulma-scheme-main-bis, #fafafa);
  border-radius: 6px;
  padding: 1rem;
}
.scroll-area {
  max-height: 500px;
  overflow-y: auto;
}
.history-list {
  list-style: none;
  margin: 0;
  padding: 0;
}
.history-list li {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  padding: 0.25rem 0;
  border-bottom: 1px solid #eee;
}
.play-icon {
  flex: 0 0 auto;
}
.play-user {
  flex: 0 0 auto;
}
.play-name {
  flex: 1 1 auto;
  min-width: 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.play-icon--clickable {
  cursor: pointer;
}
.vote-tally {
  flex: 0 0 auto;
  display: inline-flex;
  gap: 0.3rem;
  white-space: nowrap;
  cursor: default;
}
.vote-tally__up {
  color: #2e9e5b;
}
.vote-tally__down {
  color: #d14;
}
.play-time {
  flex: 0 0 auto;
  white-space: nowrap;
}
.history-list li:last-child {
  border-bottom: none;
}
</style>
