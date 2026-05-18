# API client

`schema.d.ts` contains the OpenAPI-derived TypeScript types and is
**regenerated** from the backend's `/openapi.json` by:

```sh
npm run generate:client
```

`index.ts` wraps a tiny typed [`openapi-fetch`](https://openapi-ts.dev/openapi-fetch/)
client around those types. **All** backend calls in the app go through it.
Do not hand-write `fetch`/`axios` calls to backend endpoints.
