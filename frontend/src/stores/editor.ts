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
  function queueFromExplore(url: string, title: string): void {
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
    queueFromExplore,
    consumePending,
    setRegion,
    setDuration,
    clear,
  };
});
