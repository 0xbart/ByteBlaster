<template>
  <div class="admin-panel">
    <h2 class="title is-4">Admin</h2>
    <b-tabs v-model="activeTab">
      <b-tab-item label="Users" value="users">
        <UsersTable />
      </b-tab-item>
      <b-tab-item label="Categories" value="categories">
        <CategoriesManager />
      </b-tab-item>
      <b-tab-item label="Tags" value="tags">
        <TagsManager />
      </b-tab-item>
      <b-tab-item label="Sounds" value="sounds">
        <SoundsManager />
      </b-tab-item>
    </b-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import UsersTable from "./UsersTable.vue";
import CategoriesManager from "./CategoriesManager.vue";
import TagsManager from "./TagsManager.vue";
import SoundsManager from "./SoundsManager.vue";

const activeTab = ref("users");
</script>

<style scoped>
.admin-panel {
  background: var(--bulma-scheme-main-bis, white);
  border-radius: 8px;
  padding: 1.5rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
}
</style>
