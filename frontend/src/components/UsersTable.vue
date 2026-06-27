<template>
  <div>
    <h3 class="title is-5">Users</h3>
    <table class="table is-fullwidth is-striped">
      <thead>
        <tr>
          <th>Name</th>
          <th>IP</th>
          <th>Role</th>
          <th class="has-text-right">Actions</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="u in admin.users" :key="u.id">
          <td>
            {{ u.username }}
            <span v-if="u.is_superadmin" class="tag is-warning is-light ml-2">superadmin</span>
          </td>
          <td><code>{{ u.ip }}</code></td>
          <td>
            <span v-if="u.is_admin" class="tag is-success">admin</span>
            <span v-else class="tag">user</span>
            <span v-if="u.is_mutemaster" class="tag is-info is-light ml-1">mutemaster</span>
            <span v-if="u.is_banned" class="tag is-danger ml-1">banned</span>
          </td>
          <td class="has-text-right">
            <template v-if="u.is_superadmin">
              <span class="has-text-grey">🔒 protected</span>
            </template>
            <template v-else>
              <b-button
                size="is-small"
                :type="u.is_admin ? 'is-warning' : 'is-success'"
                class="mr-2"
                @click="toggleAdmin(u.id, !u.is_admin)"
              >
                {{ u.is_admin ? "Demote" : "Promote to admin" }}
              </b-button>
              <b-button
                v-if="isSuperadmin"
                size="is-small"
                :type="u.is_mutemaster ? 'is-warning' : 'is-info'"
                icon-left="gavel"
                class="mr-2"
                @click="toggleMutemaster(u.id, !u.is_mutemaster)"
              >
                {{ u.is_mutemaster ? "Demote mutemaster" : "Make mutemaster" }}
              </b-button>
              <b-button
                v-if="isSuperadmin && u.is_banned"
                size="is-small"
                type="is-success"
                icon-left="account-check"
                class="mr-2"
                @click="unban(u.id)"
              >
                Unban
              </b-button>
              <b-dropdown
                v-else-if="isSuperadmin"
                aria-role="list"
                class="mr-2"
                @change="(min: number | null) => ban(u.id, min)"
              >
                <template #trigger>
                  <b-button size="is-small" type="is-danger" icon-left="block-helper">
                    Ban
                  </b-button>
                </template>
                <b-dropdown-item :value="5" aria-role="listitem" class="has-text-left">5 minutes</b-dropdown-item>
                <b-dropdown-item :value="30" aria-role="listitem" class="has-text-left">30 minutes</b-dropdown-item>
                <b-dropdown-item :value="60" aria-role="listitem" class="has-text-left">1 hour</b-dropdown-item>
                <b-dropdown-item :value="null" aria-role="listitem" class="has-text-left">Indefinite</b-dropdown-item>
              </b-dropdown>
              <b-button size="is-small" type="is-danger" icon-left="delete" @click="deleting = u">
                Delete
              </b-button>
            </template>
          </td>
        </tr>
      </tbody>
    </table>
    <p v-if="admin.error" class="has-text-danger">{{ admin.error }}</p>

    <ConfirmDialog
      v-if="deleting"
      title="Delete user"
      :message="`Delete user '${deleting.username}'? Their sounds will be removed as well.`"
      @confirm="confirmDelete"
      @close="deleting = null"
    />
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from "vue";
import { storeToRefs } from "pinia";
import ConfirmDialog from "./ConfirmDialog.vue";
import { useAdminStore } from "@/stores/admin";
import { useUserStore } from "@/stores/user";
import type { UserOut } from "@/api";

const admin = useAdminStore();
const userStore = useUserStore();
const { isSuperadmin } = storeToRefs(userStore);
const deleting = ref<UserOut | null>(null);

onMounted(() => {
  void admin.refreshUsers();
});

async function toggleAdmin(id: number, isAdmin: boolean): Promise<void> {
  await admin.setAdmin(id, isAdmin);
}

async function toggleMutemaster(id: number, value: boolean): Promise<void> {
  await admin.setMutemaster(id, value);
}

async function ban(id: number, durationMinutes: number | null): Promise<void> {
  await admin.setBan(id, true, durationMinutes);
}

async function unban(id: number): Promise<void> {
  await admin.setBan(id, false, null);
}

async function confirmDelete(): Promise<void> {
  const u = deleting.value;
  if (!u) return;
  await admin.removeUser(u.id);
}
</script>
