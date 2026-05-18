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
      <b-button type="is-info" icon-left="dice-6" @click="onRandom" :disabled="!visible.length">
        Random
      </b-button>
      <b-button type="is-primary" icon-left="upload" @click="showUpload = true">
        Upload sound
      </b-button>
    </div>
    <p class="search-hint has-text-grey is-size-7 mb-3">
      Tip: combine filters — <code>tag:fun</code>, <code>cat:FX</code>,
      <code>tag:"my tag"</code>, joined with <code>AND</code>. Enter plays the
      result if only one match remains.
    </p>

    <div v-if="sounds.loading" class="has-text-centered py-5">
      <b-loading :is-full-page="false" :model-value="true" />
    </div>
    <div v-else-if="!visible.length" class="has-text-centered py-5 has-text-grey">
      No sounds yet. Click "Upload sound" to add the first one.
    </div>
    <div v-else class="sound-groups">
      <section v-for="g in groupedVisible" :key="g.key" class="sound-group">
        <h3 class="sound-group__title">{{ g.label }}</h3>
        <div class="sound-grid">
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
  return named;
});

onMounted(() => {
  void sounds.refresh();
  void nextTick(() => filterInput.value?.focus?.());
});

function onRandom(): void {
  const list = visible.value;
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
.sound-groups {
  margin-top: 1rem;
}
.sound-group + .sound-group {
  margin-top: 1.25rem;
}
.sound-group__title {
  font-size: 0.85rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: #555;
  margin-bottom: 0.5rem;
}
.sound-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 0.75rem;
}
</style>
