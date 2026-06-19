import { defineStore } from "pinia";
import { ref } from "vue";

export const useEditorStore = defineStore("editor", () => {
  // Exactly one of these is set; the rest are derived metadata.
  const soundId = ref<number | null>(null);
  const sourceUrl = ref<string | null>(null);
  const sourceAudioUrl = ref<string | null>(null); // URL wavesurfer fetches
  const sourceTitle = ref<string>("");
  const startSec = ref(0);
  const endSec = ref(0);
  const durationSec = ref(0);
  const pending = ref<{ url?: string; soundId?: number; audioUrl: string; title: string } | null>(null);

  function loadSound(id: number, title: string, audioUrl: string): void {
    soundId.value = id;
    sourceUrl.value = null;
    sourceAudioUrl.value = audioUrl;
    sourceTitle.value = title;
    startSec.value = 0;
    endSec.value = 0;
  }
  function loadUrl(url: string, title: string): void {
    soundId.value = null;
    sourceUrl.value = url;
    sourceAudioUrl.value = url;
    sourceTitle.value = title;
    startSec.value = 0;
    endSec.value = 0;
  }
  // External source where the browser can't fetch the raw URL directly (CORS),
  // so the waveform loads from a same-origin proxy while trim uses the real URL.
  function loadExternal(url: string, audioUrl: string, title: string): void {
    soundId.value = null;
    sourceUrl.value = url;
    sourceAudioUrl.value = audioUrl;
    sourceTitle.value = title;
    startSec.value = 0;
    endSec.value = 0;
  }
  function queueFromExplore(url: string, title: string): void {
    const audioUrl = `/api/explore/proxy?url=${encodeURIComponent(url)}`;
    pending.value = { url, audioUrl, title };
  }
  // Local-library file: same-origin, so the browser can fetch the real URL
  // directly (no proxy). Trim uses the same URL; the backend resolves it to
  // disk via the /api/explore/local/file?rel=… branch.
  function queueLocal(url: string, title: string): void {
    pending.value = { url, audioUrl: url, title };
  }
  // YouTube preview: served same-origin from /api/explore/youtube/preview/…,
  // so the browser fetches it directly (no proxy — the myinstants proxy would
  // reject it). Trim forwards the same URL; the backend resolves it to disk
  // via the _YT_PREVIEW_RE branch.
  function queueFromYoutube(url: string, title: string): void {
    pending.value = { url, audioUrl: url, title };
  }
  function consumePending(): { url?: string; soundId?: number; audioUrl: string; title: string } | null {
    const p = pending.value;
    pending.value = null;
    return p;
  }
  function setRegion(start: number, end: number): void {
    startSec.value = start;
    endSec.value = end;
  }
  function setDuration(d: number): void {
    durationSec.value = d;
  }
  function clear(): void {
    soundId.value = null;
    sourceUrl.value = null;
    sourceAudioUrl.value = null;
    sourceTitle.value = "";
    startSec.value = 0;
    endSec.value = 0;
    durationSec.value = 0;
  }
  return {
    soundId,
    sourceUrl,
    sourceAudioUrl,
    sourceTitle,
    startSec,
    endSec,
    durationSec,
    pending,
    loadSound,
    loadUrl,
    loadExternal,
    queueFromExplore,
    queueLocal,
    queueFromYoutube,
    consumePending,
    setRegion,
    setDuration,
    clear,
  };
});
