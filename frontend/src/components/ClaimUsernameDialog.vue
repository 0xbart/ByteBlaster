<template>
  <div class="modal is-active">
    <div class="modal-background" />
    <div class="modal-card">
      <header class="modal-card-head">
        <p class="modal-card-title">Welcome to ByteBlaster</p>
      </header>
      <section class="modal-card-body">
        <p class="mb-3">
          We don't recognize this IP address (<code>{{ user.ip }}</code>) yet.
          Pick a username — it will be linked to your IP.
        </p>
        <b-field
          label="Username"
          :type="user.claimError ? 'is-danger' : ''"
          :message="user.claimError ?? ''"
        >
          <b-input
            v-model="username"
            placeholder="e.g. Bram"
            maxlength="64"
            :disabled="submitting"
            @keyup.enter="submit"
            autofocus
          />
        </b-field>
      </section>
      <footer class="modal-card-foot">
        <b-button
          type="is-primary"
          :loading="submitting"
          :disabled="!isValid"
          @click="submit"
        >
          Claim
        </b-button>
      </footer>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import { useUserStore } from "@/stores/user";

const user = useUserStore();
const username = ref("");
const submitting = ref(false);

const isValid = computed(() => /^[A-Za-z0-9_\- ]{2,64}$/.test(username.value));

async function submit(): Promise<void> {
  if (!isValid.value || submitting.value) return;
  submitting.value = true;
  await user.claim(username.value.trim());
  submitting.value = false;
}
</script>
