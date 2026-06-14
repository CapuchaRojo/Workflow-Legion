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

## Mission Control positioning

The showcase integrates the NativelyAI / Native.Builder presentation layer without replacing the working runtime contract:

- Band coordinates agents and provides visible proof through room messages, mentions, handoffs, shared context, and task state.
- The backend executes deterministic autonomous runtime and state-machine logic, then exports sanitized Mission Control JSON.
- NativelyAI / Native.Builder is the Mission Control and productization layer for demos, screenshots, and stakeholder storytelling.
- AI/ML API and Featherless remain provider support layers only.

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

