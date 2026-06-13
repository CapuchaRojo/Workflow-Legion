# Workflow Legion Frontend Showcase

Static Vite + React + TypeScript showcase for Workflow Legion: Cyber Incident Command Room.

## Local setup

```cmd
npm install
npm run build
```

For local viewing during development:

```cmd
npm run dev
```

This showcase does not call the backend, does not use Supabase or auth, and does not require environment files or API keys. Mission Control can optionally read a sanitized local JSON file from `public\mission-control-status.json`; if that file is missing, it falls back to built-in demo data.

## Live Mission Control export

From the repository root, run the autonomous runtime with the safe frontend export path:

```cmd
backend\.venv\Scripts\python.exe backend\run_autonomous_agents.py --run-id studio-001 --poll-interval 3 --max-turns 8 --message-limit 25 --stop-after-complete --debug-receive --frontend-studio-export frontend-showcase\public\mission-control-status.json
```

Then start the showcase:

```cmd
cd frontend-showcase
npm run dev
```

Band remains the collaboration fabric and proof surface. The frontend is only a Mission Control visualization layer over sanitized runtime status.

