<template>
  <div class="sound-button">
    <span v-if="sound.duration_ms" class="duration-badge">
      {{ formatDuration(sound.duration_ms) }}
    </span>
    <button
      class="button is-medium is-fullwidth"
      :class="{
        'is-dark': theme.isDark,
        'no-tags': !sound.tags.length,
        'has-tags': sound.tags.length,
      }"
      :title="tooltip"
      @click="onPlay"
    >
      <span class="sound-label">{{ sound.display_name }}</span>
      <span v-if="sound.tags.length" class="tag-chips">
        <span v-for="t in sound.tags" :key="t" class="tag is-light tag-chip">#{{ t }}</span>
      </span>
    </button>
    <div class="overlay-actions">
      <button
        v-if="canEdit"
        class="button is-small is-info action-btn"
        title="Edit"
        tabindex="-1"
        @click.stop="editOpen = true"
      >
        <i class="fas fa-pencil" aria-hidden="true" />
      </button>
      <button
        class="button is-small is-link action-btn"
        title="Schedule"
        tabindex="-1"
        @click.stop="scheduleOpen = true"
      >
        <i class="fas fa-clock" aria-hidden="true" />
      </button>
      <button
        v-if="canDelete"
        class="button is-small is-danger action-btn"
        title="Delete"
        tabindex="-1"
        @click.stop="deleteOpen = true"
      >
        <i class="fas fa-trash" aria-hidden="true" />
      </button>
      <button
        class="button is-small action-btn favorite-btn"
        :class="[
          sound.is_favorite
            ? 'action-btn--pinned favorite-btn--active'
            : 'is-light',
        ]"
        :title="sound.is_favorite ? 'Remove from favorites' : 'Add to favorites'"
        tabindex="-1"
        @click.stop="onToggleFavorite($event)"
      >
        <i class="fas fa-star" aria-hidden="true" />
      </button>
    </div>

    <EditSoundDialog v-if="editOpen" :sound="sound" @close="editOpen = false" />
    <ScheduleDialog
      v-if="scheduleOpen"
      :sound-id="sound.id"
      :sound-name="sound.display_name"
      @close="scheduleOpen = false"
    />
    <ConfirmDialog
      v-if="deleteOpen"
      title="Delete sound"
      :message="`Delete '${sound.display_name}'? This cannot be undone.`"
      @confirm="confirmDelete"
      @close="deleteOpen = false"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import EditSoundDialog from "./EditSoundDialog.vue";
import ConfirmDialog from "./ConfirmDialog.vue";
import ScheduleDialog from "./ScheduleDialog.vue";
import { useSoundsStore } from "@/stores/sounds";
import { useUserStore } from "@/stores/user";
import { useThemeStore } from "@/stores/theme";
import type { SoundOut } from "@/api";

const props = defineProps<{ sound: SoundOut }>();
const sounds = useSoundsStore();
const user = useUserStore();
const theme = useThemeStore();
const editOpen = ref(false);
const deleteOpen = ref(false);
const scheduleOpen = ref(false);

const canEdit = computed(() => user.isAdmin);
const canDelete = computed(
  () => user.me?.id === props.sound.uploaded_by_user_id || user.isAdmin,
);
const tooltip = computed(() =>
  props.sound.tags.length
    ? `${props.sound.display_name} — ${props.sound.tags.map((t) => `#${t}`).join(" ")}`
    : props.sound.display_name,
);

function onPlay(): void {
  void sounds.play(props.sound.id);
}

function confirmDelete(): void {
  void sounds.remove(props.sound.id);
}

function onToggleFavorite(ev: MouseEvent): void {
  (ev.currentTarget as HTMLElement | null)?.blur();
  if (props.sound.is_favorite) void sounds.unfavorite(props.sound.id);
  else void sounds.favorite(props.sound.id);
}

function formatDuration(ms: number): string {
  const s = Math.round(ms / 1000);
  if (s < 60) return `${s}s`;
  const m = Math.floor(s / 60);
  const rem = s % 60;
  return rem === 0 ? `${m}m` : `${m}m${rem}s`;
}
</script>

<style scoped>
.sound-button {
  position: relative;
}
.duration-badge {
  position: absolute;
  top: -6px;
  left: -6px;
  z-index: 2;
  min-width: 28px;
  height: 20px;
  padding: 0 6px;
  border-radius: 999px;
  background: var(--bulma-scheme-main-ter, rgba(0, 0, 0, 0.55));
  color: var(--bulma-text, #fff);
  font-size: 0.7rem;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
  pointer-events: none;
  opacity: 0;
  transition: opacity 0.15s ease-in-out;
}
.sound-button:hover .duration-badge,
.sound-button:focus-within .duration-badge {
  opacity: 0.55;
}
.sound-button :deep(.button.is-fullwidth) {
  min-height: 2.5em;
  height: auto;
}
.sound-label {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  display: block;
  max-width: 100%;
  font-size: 0.8rem;
}
.sound-button :deep(.button.no-tags) {
  align-items: flex-start;
  padding-top: 0.6em;
}
.has-tags .sound-label {
  transform: translateY(-10px);
}
.tag-chips {
  position: absolute;
  bottom: 4px;
  right: 6px;
  display: flex;
  gap: 4px;
  max-width: 85%;
  overflow: hidden;
  pointer-events: none;
}
.tag-chip {
  font-size: 0.72rem;
  font-weight: 600;
  height: auto;
  padding: 1px 7px;
}
.overlay-actions {
  position: absolute;
  top: -8px;
  right: -8px;
  display: flex;
  gap: 4px;
}
.action-btn {
  border-radius: 50%;
  padding: 0;
  width: 28px;
  height: 28px;
  line-height: 1;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  pointer-events: none;
  transition: opacity 0.12s ease-in-out;
}
.sound-button:hover .action-btn,
.sound-button:focus-within .action-btn,
.action-btn--pinned {
  opacity: 1;
  pointer-events: auto;
}
.favorite-btn--active {
  background-color: hsl(48, 95%, 65%);
  color: hsl(36, 60%, 22%);
  border-color: transparent;
}
.favorite-btn--active:hover {
  background-color: hsl(48, 95%, 58%);
}
</style>
