<template>
  <div class="modal is-active">
    <div class="modal-background" @click="emit('close')" />
    <div class="modal-card">
      <header class="modal-card-head">
        <p class="modal-card-title">
          Live users
          <span class="tag is-success ml-2">{{ presence.count }}</span>
        </p>
        <button class="delete" aria-label="close" @click="emit('close')" />
      </header>
      <section class="modal-card-body">
        <table v-if="presence.users.length" class="table is-fullwidth is-striped">
          <thead>
            <tr>
              <th>Name</th>
              <th>IP</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="u in presence.users" :key="u.id">
              <td>
                {{ u.username }}
                <span v-if="u.id === me?.id" class="tag is-info is-light ml-2">you</span>
              </td>
              <td><code>{{ u.ip }}</code></td>
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
import { usePresenceStore } from "@/stores/presence";
import { useUserStore } from "@/stores/user";

const emit = defineEmits<(e: "close") => void>();
const presence = usePresenceStore();
const userStore = useUserStore();
const { me } = storeToRefs(userStore);
</script>
