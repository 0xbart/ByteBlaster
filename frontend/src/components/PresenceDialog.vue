<template>
  <div class="modal is-active">
    <div class="modal-background" @click="emit('close')" />
    <div class="modal-card" :class="{ 'modal-card--wide': isSuperadmin }">
      <header class="modal-card-head">
        <p class="modal-card-title">
          Live users
          <span class="tag is-success ml-2">
            {{ presence.count }} user{{ presence.count === 1 ? "" : "s" }}
          </span>
        </p>
        <button class="delete" aria-label="close" @click="emit('close')" />
      </header>
      <section class="modal-card-body">
        <table v-if="presence.users.length" class="table is-fullwidth is-striped">
          <thead>
            <tr>
              <th>Name</th>
              <th>Role</th>
              <th>Volume</th>
              <th>IP</th>
              <th v-if="isSuperadmin">Theme</th>
              <th v-if="isSuperadmin">Ban</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="u in presence.users" :key="u.id">
              <td>
                {{ u.username }}
                <span v-if="u.id === me?.id" class="tag is-info is-light ml-2">you</span>
              </td>
              <td>
                <span v-if="u.is_superadmin" class="tag is-warning is-light">superadmin</span>
                <span v-else-if="u.is_admin" class="tag is-success">admin</span>
                <span v-else class="tag">user</span>
              </td>
              <td>
                <span class="is-flex is-align-items-center">
                  <b-icon
                    :icon="volumeIcon(u.volume ?? 100)"
                    pack="fas"
                    size="is-small"
                    class="mr-2"
                  />
                  <span>{{ u.volume ?? 100 }}%</span>
                </span>
              </td>
              <td><code>{{ u.ip }}</code></td>
              <td v-if="isSuperadmin">
                <div v-if="u.id !== me?.id" class="select is-small">
                  <select :value="''" @change="applyTheme(u, $event)">
                    <option value="" disabled>Set theme…</option>
                    <option v-for="(p, i) in themePresets" :key="p.label" :value="i">
                      {{ p.label }}
                    </option>
                  </select>
                </div>
                <span v-else class="has-text-grey">—</span>
              </td>
              <td v-if="isSuperadmin">
                <template v-if="u.id === me?.id || u.is_superadmin">
                  <span class="has-text-grey">—</span>
                </template>
                <b-button
                  v-else-if="u.is_banned"
                  size="is-small"
                  type="is-success"
                  icon-left="account-check"
                  @click="unban(u)"
                >
                  Unban
                </b-button>
                <div v-else class="select is-small">
                  <select :value="''" @change="applyBan(u, $event)">
                    <option value="" disabled>Ban…</option>
                    <option v-for="(b, i) in banPresets" :key="b.label" :value="i">
                      {{ b.label }}
                    </option>
                  </select>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
        <p v-else class="has-text-grey has-text-centered">
          No one is connected.
        </p>
      </section>
      <footer class="modal-card-foot">
        <b-button @click="emit('close')">Close</b-button>
      </footer>
    </div>
  </div>
</template>

<script setup lang="ts">
import { storeToRefs } from "pinia";
import { usePresenceStore, type PresenceUser } from "@/stores/presence";
import { useEscapeClose } from "@/composables/useEscapeClose";
import { useUserStore } from "@/stores/user";
import { useWsStore } from "@/stores/ws";
import { useAdminStore } from "@/stores/admin";
import type { ThemeMode, Skin } from "@/stores/theme";

const emit = defineEmits<(e: "close") => void>();
useEscapeClose(() => emit("close"));
const presence = usePresenceStore();
const userStore = useUserStore();
const { me, isSuperadmin } = storeToRefs(userStore);
const ws = useWsStore();
const admin = useAdminStore();

interface ThemePreset {
  label: string;
  mode: ThemeMode;
  skin: Skin;
}

const themePresets: ThemePreset[] = [
  { label: "Light", mode: "light", skin: "default" },
  { label: "Dark", mode: "dark", skin: "default" },
  { label: "Cyber", mode: "dark", skin: "cyber" },
  { label: "Pink", mode: "light", skin: "pink" },
  { label: "Money", mode: "light", skin: "money" },
  { label: "Government", mode: "light", skin: "government" },
];

function applyTheme(u: PresenceUser, ev: Event): void {
  const sel = ev.target as HTMLSelectElement;
  const p = themePresets[Number(sel.value)];
  if (!p) return;
  ws.setUserTheme(u.id, p.mode, p.skin);
  // Reset so the same preset can be re-applied and the label stays neutral.
  sel.value = "";
}

interface BanPreset {
  label: string;
  durationMinutes: number | null;
}

const banPresets: BanPreset[] = [
  { label: "5 minutes", durationMinutes: 5 },
  { label: "30 minutes", durationMinutes: 30 },
  { label: "1 hour", durationMinutes: 60 },
  { label: "Indefinite", durationMinutes: null },
];

function applyBan(u: PresenceUser, ev: Event): void {
  const sel = ev.target as HTMLSelectElement;
  const b = banPresets[Number(sel.value)];
  sel.value = "";
  if (!b) return;
  void admin.setBan(u.id, true, b.durationMinutes);
}

function unban(u: PresenceUser): void {
  void admin.setBan(u.id, false, null);
}

function volumeIcon(v: number): string {
  if (v === 0) return "volume-xmark";
  if (v <= 33) return "volume-low";
  if (v <= 66) return "volume";
  return "volume-high";
}
</script>

<style scoped>
/* Superadmin rows carry extra columns (Theme + Ban); widen the card so the
   table fits without horizontal scrolling. Bulma's default is 640px. */
@media screen and (min-width: 769px) {
  .modal-card--wide {
    width: 850px;
    max-width: 850px;
  }
}
</style>
