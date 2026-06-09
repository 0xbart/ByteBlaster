// Typed API client — single source of truth for backend calls.
// `schema.d.ts` is regenerated from the backend's OpenAPI spec
// (see `npm run generate:client` or the frontend Dockerfile).

import createClient from "openapi-fetch";
import type { paths, components } from "./schema";

export const api = createClient<paths>({ baseUrl: "" });

export type UserOut = components["schemas"]["UserOut"];
export type MeOut = components["schemas"]["MeOut"];
export type SoundOut = components["schemas"]["SoundOut"];
export type PlayOut = components["schemas"]["PlayOut"];
export type CategoryOut = components["schemas"]["CategoryOut"];
export type TagOut = components["schemas"]["TagOut"];
export type SoundStatOut = components["schemas"]["SoundStatOut"];
export type UserStatOut = components["schemas"]["UserStatOut"];
export type CategoryStatOut = components["schemas"]["CategoryStatOut"];
export type OverviewStatOut = components["schemas"]["OverviewStatOut"];
export type ExploreResult = components["schemas"]["ExploreResult"];
export type ExploreSearchOut = components["schemas"]["ExploreSearchOut"];
export type YoutubeFetchIn = components["schemas"]["YoutubeFetchIn"];
export type YoutubeFetchOut = components["schemas"]["YoutubeFetchOut"];
export type EditorTrimIn = components["schemas"]["EditorTrimIn"];
