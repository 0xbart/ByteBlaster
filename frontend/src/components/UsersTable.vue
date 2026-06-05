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

async function confirmDelete(): Promise<void> {
  const u = deleting.value;
  if (!u) return;
  await admin.removeUser(u.id);
}
</script>
