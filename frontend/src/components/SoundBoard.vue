<template>
  <div>
    <div class="board-actions">
      <b-input
        ref="filterInput"
        v-model="filter"
        placeholder="e.g. airhorn"
        icon="magnify"
        clearable
        autofocus
        class="filter-input"
        @keyup.enter="onFilterEnter"
      />
      <b-button type="is-info" icon-left="dice-6" @click="onRandom" :disabled="!sounds.sortedByName.length">
        Random
      </b-button>
      <b-button type="is-primary" icon-left="upload" @click="showUpload = true">
        Upload sound
      </b-button>
    </div>
    <p class="search-hint has-text-grey is-size-7 mb-1">
      Tip: combine filters — <code>tag:fun</code>, <code>cat:FX</code>,
      <code>tag:"my tag"</code>, joined with <code>AND</code>. Enter plays the
      result if only one match remains.
    </p>
    <p class="search-hint has-text-grey is-size-7 mb-3">
      Tip 2: click a category header to collapse or expand it.
      <a class="collapse-link" @click="expandAll">Expand all</a>
      <span class="has-text-grey-light"> · </span>
      <a class="collapse-link" @click="collapseAll">Collapse all</a>
    </p>

    <div v-if="sounds.loading" class="has-text-centered py-5">
      <b-loading :is-full-page="false" :model-value="true" />
    </div>
    <div v-else-if="!visible.length" class="has-text-centered py-5 has-text-grey">
      No sounds yet. Click "Upload sound" to add the first one.
    </div>
    <div v-else class="sound-groups">
      <section v-for="g in groupedVisible" :key="g.key" class="sound-group">
        <h3
          class="sound-group__title"
          role="button"
          @click="toggleGroup(g.key)"
        >
          <b-icon
            :icon="isCollapsed(g.key) ? 'circle-chevron-up' : 'circle-chevron-down'"
            pack="fas"
            size="is-small"
            class="mr-2"
          />
          <span>{{ g.label }}</span>
          <span class="sound-group__count">{{ g.sounds.length }}</span>
        </h3>
        <div v-show="!isCollapsed(g.key)" class="sound-grid">
          <SoundButton v-for="s in g.sounds" :key="s.id" :sound="s" />
        </div>
      </section>
    </div>

    <UploadDialog v-if="showUpload" @close="showUpload = false" />
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, ref } from "vue";
import SoundButton from "./SoundButton.vue";
import UploadDialog from "./UploadDialog.vue";
import { useSoundsStore } from "@/stores/sounds";

const sounds = useSoundsStore();
const showUpload = ref(false);
const filter = ref("");
const filterInput = ref<{ focus?: () => void } | null>(null);
const collapsed = ref<Set<string>>(new Set());

function isCollapsed(key: string): boolean {
  return collapsed.value.has(key);
}
function toggleGroup(key: string): void {
  const next = new Set(collapsed.value);
  if (next.has(key)) next.delete(key);
  else next.add(key);
  collapsed.value = next;
}
function expandAll(): void {
  collapsed.value = new Set();
}
function collapseAll(): void {
  collapsed.value = new Set(groupedVisible.value.map((g) => g.key));
}

interface ParsedQuery {
  tags: string[];
  categories: string[];
  text: string;
}

/**
 * Tokenize a Kibana-ish query: supports `tag:foo`, `cat:bar` (or `category:bar`),
 * quoted values for multi-word tokens (`tag:"my tag"`), and an optional `AND`
 * literal between clauses (case-insensitive). Anything that isn't a `key:value`
 * clause becomes free-text matched against name/tags/category.
 */
function parseQuery(raw: string): ParsedQuery {
  const tags: string[] = [];
  const categories: string[] = [];
  const rest: string[] = [];

  const tokenRe = /"([^"]*)"|(\S+)/g;
  let m: RegExpExecArray | null;
  while ((m = tokenRe.exec(raw)) !== null) {
    const tok = (m[1] ?? m[2] ?? "").trim();
    if (!tok || /^and$/i.test(tok)) continue;
    const kv = /^(tag|cat|category):(?:"([^"]*)"|(.*))$/i.exec(tok);
    if (kv) {
      const key = kv[1].toLowerCase();
      const val = (kv[2] ?? kv[3] ?? "").toLowerCase().trim();
      if (!val) continue;
      if (key === "tag") tags.push(val);
      else categories.push(val);
    } else {
      rest.push(tok.toLowerCase());
    }
  }
  return { tags, categories, text: rest.join(" ") };
}

const visible = computed(() => {
  const q = parseQuery(filter.value);
  const list = sounds.sortedByName;
  if (!q.tags.length && !q.categories.length && !q.text) return list;
  return list.filter((s) => {
    const sName = s.display_name.toLowerCase();
    const sCat = (s.category_name ?? "").toLowerCase();
    const sTags = s.tags.map((t) => t.toLowerCase());

    // Every tag:X clause must match at least one of the sound's tags.
    if (!q.tags.every((t) => sTags.some((st) => st.includes(t)))) return false;
    // Every cat:X clause must match the sound's category name.
    if (!q.categories.every((c) => sCat.includes(c))) return false;
    // Free-text matches name OR any tag OR category.
    if (q.text) {
      const hit =
        sName.includes(q.text) ||
        sTags.some((st) => st.includes(q.text)) ||
        sCat.includes(q.text);
      if (!hit) return false;
    }
    return true;
  });
});

type SoundItem = (typeof sounds.sortedByName)[number];
interface SoundGroup {
  key: string;
  label: string;
  sounds: SoundItem[];
}
const UNCATEGORIZED_KEY = "__uncategorized__";
const FAVORITES_KEY = "__favorites__";

const groupedVisible = computed<SoundGroup[]>(() => {
  const byCat = new Map<string | null, SoundItem[]>();
  for (const s of visible.value) {
    const k = s.category_name ?? null;
    const bucket = byCat.get(k);
    if (bucket) bucket.push(s);
    else byCat.set(k, [s]);
  }

  const named: SoundGroup[] = [];
  for (const [name, items] of byCat.entries()) {
    if (name === null) continue;
    named.push({ key: name, label: name, sounds: items });
  }
  named.sort((a, b) => a.label.localeCompare(b.label));

  const uncategorized = byCat.get(null);
  if (uncategorized && uncategorized.length > 0) {
    named.push({ key: UNCATEGORIZED_KEY, label: "Uncategorized", sounds: uncategorized });
  }

  const favs = visible.value.filter((s) => s.is_favorite);
  if (favs.length > 0) {
    return [{ key: FAVORITES_KEY, label: "Favorites", sounds: favs }, ...named];
  }
  return named;
});

onMounted(() => {
  void sounds.refresh();
  void nextTick(() => filterInput.value?.focus?.());
});

function onRandom(): void {
  const list = sounds.sortedByName;
  if (!list.length) return;
  const pick = list[Math.floor(Math.random() * list.length)];
  void sounds.play(pick.id);
}

function onFilterEnter(): void {
  // If the search has narrowed down to exactly one sound, play it.
  if (visible.value.length === 1) {
    void sounds.play(visible.value[0].id);
    filter.value = "";
    void nextTick(() => filterInput.value?.focus?.());
  }
}
</script>

<style scoped>
.board-actions {
  display: flex;
  gap: 0.75rem;
  margin-bottom: 0.4rem;
  align-items: center;
  flex-wrap: wrap;
}
.search-hint code {
  background: var(--bulma-code-background, rgba(0, 0, 0, 0.06));
  padding: 0 0.25rem;
  border-radius: 3px;
}
.filter-input {
  flex: 1 1 240px;
  min-width: 200px;
}
.collapse-link {
  cursor: pointer;
  color: inherit;
  text-decoration: none;
  border-bottom: 1px dotted currentColor;
  opacity: 0.7;
}
.collapse-link:hover {
  opacity: 1;
}
.sound-groups {
  margin-top: 1rem;
}
.sound-group + .sound-group {
  margin-top: 1.25rem;
}
.sound-group__title {
  display: flex;
  align-items: center;
  font-size: 0.85rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: #555;
  margin-bottom: 0.5rem;
  padding-bottom: 0.35rem;
  border-bottom: 1px solid var(--bulma-border-weak, rgba(128, 128, 128, 0.22));
  cursor: pointer;
  user-select: none;
}
.sound-group__count {
  margin-left: 0.5rem;
  background: var(--bulma-scheme-main-ter, rgba(0, 0, 0, 0.1));
  color: inherit;
  border-radius: 999px;
  padding: 0 0.5rem;
  font-size: 0.75rem;
}
.sound-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 0.75rem;
}
</style>
