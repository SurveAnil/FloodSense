# Deploy the FloodSense mentor demo

This setup hosts the React frontend on Vercel and the FastAPI service on
Render. The Vercel rewrites in `vercel.json` proxy `/api/*` and `/health` to
Render so browser requests and session cookies remain on the Vercel site.

This configuration intentionally enables public demo accounts for presentation
only. The risk data is replay data, and the free Render service uses an
ephemeral filesystem: reports, sessions, and other SQLite changes can be lost
when the service restarts or redeploys. Do not store real or sensitive data in
this demo deployment.

## 1. Deploy the API to Render

1. Push the repository to GitHub and sign in to [Render](https://render.com/).
2. Select **New** → **Blueprint** and choose the FloodSense repository.
3. Allow Render to read the root `render.yaml` and create the `floodsense-api`
   web service. The manifest installs `backend/requirements.txt`, starts
   Uvicorn on Render's assigned port, sets replay/demo mode, and checks
   `/health`.
4. Wait for the first deployment to finish. Open the service URL; it should be
   `https://floodsense-api.onrender.com/health` and return JSON containing
   `"status":"ok"`, `"data_mode":"replay"`, and `"demo_mode":"true"`.
5. If Render assigns a different public hostname, update the two Render
   destinations in `vercel.json` to that exact HTTPS hostname and push the
   change before deploying the frontend.

The API provisions its three demo roles during startup when
`FLOODSENSE_DEMO_MODE=true`. No demo passwords are needed; use the role buttons
on the sign-in page. For any non-demo deployment, turn this setting off and
provision real users from a trusted backend environment.

## 2. Deploy the frontend to Vercel

1. In Vercel, open the FloodSense project and confirm its Git repository points
   to this repository with `master` as the production branch.
2. In **Settings** → **Environment Variables**, remove `VITE_API_BASE_URL` if
   it is set to `http://localhost:8000` or another API hostname. With no
   override, the production frontend calls its own origin and Vercel proxies
   those API requests to Render.
3. Trigger a new production deployment (use **Redeploy** after deleting the
   variable, or push a commit after updating `vercel.json`).
4. Open the Vercel production domain. The three **Development/demo accounts**
   buttons should appear after the API health check reports demo mode enabled.
   Use a role button to sign in.

Satellite and topographic basemaps require an ArcGIS API key. Add
`VITE_ARCGIS_API_KEY` in Vercel **Settings** → **Environment Variables** for
Production, Preview, and Development, then redeploy so Vite includes it in the
build. This is a public browser key: restrict its privileges and allowed
referrers to your application domains. Without it, ArcGIS basemaps remain
disabled. Never put backend secrets in `VITE_*` variables; Vite embeds these
values in public browser code.

The backend retrieves current Pune weather from the public Open-Meteo API
without a key. Its observation freshness is checked separately from the
replay-based risk predictions; temporary provider errors or rate limits appear
as an unavailable source status.

## 3. Verify the live connection

Check these URLs using the Vercel domain:

- `https://YOUR-VERCEL-DOMAIN/health` should return the Render health JSON.
- `https://YOUR-VERCEL-DOMAIN/api/auth/me` should return `401` when signed out;
  this confirms the API route is reached and authentication is required.
- On the sign-in page, confirm the demo buttons appear and a role button opens
  the dashboard.

If the Vercel health URL returns the application HTML, the Vercel rewrite did
not match; check that `/health` and `/api/(.*)` precede the single-page-app
fallback in `vercel.json`. If it returns a Render error, inspect the Render
service's deploy and runtime logs. A free Render service may sleep while idle,
so its first request can take longer while it starts.

## Persistence

The included free-tier setup stores SQLite data at `/tmp/floodsense.sqlite3`.
That is suitable for a temporary mentor demo, not durable storage. For durable
records, use a paid Render instance with a persistent disk mounted at `/var/data`
and set `FLOODSENSE_DB_PATH=/var/data/floodsense.sqlite3`, or migrate the
application's persistence layer to a managed database before production use.
