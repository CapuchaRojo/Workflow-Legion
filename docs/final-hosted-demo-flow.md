# Final Hosted Demo Flow

This is the concise judge guide for the final public hosted Workflow Legion demo.

## Public URLs

- Frontend showcase: <https://workflow-legion-frontend-production.up.railway.app/>
- Backend health: <https://workflow-legion-production.up.railway.app/health>
- Backend sanitized status: <https://workflow-legion-production.up.railway.app/mission-control-status>

## Demo Flow

1. Open the Band room.
2. Open the public frontend:
   <https://workflow-legion-frontend-production.up.railway.app/>
3. Post in Band:
   `@Workflow Triage Remote Agent AUTO:START WL-INC-003`
4. Show Band agent posts:
   `Triage -> Threat Intel + Forensics -> Compliance -> Incident Commander`
5. Refresh the frontend and show the live hosted Mission Control update.
6. Open backend `/mission-control-status` if needed as raw sanitized proof.

## Architecture

Workflow Legion uses Band as the live agent collaboration fabric and proof surface. A Railway-hosted backend listens for Band triggers, runs the deterministic five-agent incident workflow, posts visible agent handoffs back into Band, and exports a sanitized Mission Control status feed. A public Railway-hosted frontend displays that live status for judges without exposing secrets or requiring local terminals.

Native.Builder/NativelyAI informed the showcase/productization layer and visual command-center direction. The final live deployment uses Railway for the hosted frontend and backend runtime.

## Validated Proof Boundary

- Band room trigger successfully starts the hosted workflow.
- Railway-hosted backend processes the five-agent chain.
- Agents visibly post in Band:
  `Triage -> Threat Intel + Forensics -> Compliance -> Incident Commander`.
- Public Railway frontend reads the hosted sanitized Mission Control status.
- No local terminal listener is required for the public demo.
- Commander is terminal; there is no downstream handoff after Commander.
- AI/ML API and Featherless are optional provider support layers.

## Recording Safety

Do not record or commit secrets, Band IDs, room IDs, chat IDs, API keys,
sponsor codes, QR codes, redemption links, `.env` values, private credentials,
runtime proof JSON, Railway Variables screens, screenshots with secrets,
`node_modules`, `dist`, or build output.
