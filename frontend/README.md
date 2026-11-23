# Loyaltics UI (React + Vite)

    npm install
    npm run dev        # http://localhost:5173

Start your FastAPI backend on port 8000 first. Requests to /api/* are proxied
to http://localhost:8000 (see vite.config.js), so no CORS setup is needed in dev.

For production, set VITE_API_URL=https://your-api-host and enable CORSMiddleware on the backend.
