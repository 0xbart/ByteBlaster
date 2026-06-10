// Hackertyper keystroke effect for the cyber skin: typing anywhere outside a
// real input spawns floating green glyphs near the cursor. Thin wrapper over the
// shared useFloatingTyper; active only while skin === "cyber".

import { useFloatingTyper } from "./useFloatingTyper";

const SNIPPETS = [
  "0x1F",
  "sudo",
  "rm -rf",
  "01001",
  "ACCESS",
  "ping",
  "root@",
  "0xDEAD",
  "::1",
  "grep -r",
  "exec()",
  "<script>",
  "0b1010",
  "ssh",
  "kernel",
];

export function useHackerTyper(): void {
  useFloatingTyper("cyber", SNIPPETS, "hacker-glyph");
}
