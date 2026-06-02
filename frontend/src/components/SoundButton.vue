<template>
  <div class="sound-button">
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
        v-if="canDelete"
        class="button is-small is-danger action-btn"
        title="Delete"
        tabindex="-1"
        @click.stop="deleteOpen = true"
      >
        <i class="fas fa-trash" aria-hidden="true" />
      </button>
    </div>

    <EditSoundDialog v-if="editOpen" :sound="sound" @close="editOpen = false" />
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
</script>

<style scoped>
.sound-button {
  position: relative;
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
  opacity: 0;
  pointer-events: none;
  transition: opacity 0.12s ease-in-out;
}
.sound-button:hover .overlay-actions,
.sound-button:focus-within .overlay-actions {
  opacity: 1;
  pointer-events: auto;
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
}
</style>
