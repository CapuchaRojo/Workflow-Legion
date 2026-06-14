# Incident Sequence - WL-INC-001

This sequence shows the current validated live path. Band is the visible collaboration fabric. The backend executes deterministic runtime logic, stores local JSON state, and advances downstream work through an in-process handoff queue after successful visible Band delivery.

```mermaid
sequenceDiagram
    participant Human as Human Operator
    participant Band as Band Room
    participant Runtime as Backend Runtime
    participant Queue as In-process Handoff Queue
    participant Triage as Triage Remote Band Identity
    participant ThreatIntel as Threat Intel Remote Band Identity
    participant Forensics as Forensics Remote Band Identity
    participant Compliance as Compliance Remote Band Identity
    participant Commander as Incident Commander Remote Band Identity
    participant Mission as Mission Control Export

    Human->>Band: @Workflow Triage Remote Agent AUTO:START WL-INC-001
    Runtime->>Band: Poll receive API
    Band-->>Runtime: Fresh AUTO:START message
    Runtime->>Runtime: Match Triage trigger and create run state

    Runtime->>Triage: Execute Triage role logic
    Triage->>Band: Post findings with Threat Intel and Forensics mentions
    Band-->>Runtime: Delivery status 201
    Runtime->>Queue: Enqueue Threat Intel and Forensics after delivery

    Queue-->>Runtime: Threat Intel work item
    Runtime->>ThreatIntel: Execute Threat Intel role logic
    ThreatIntel->>Band: Post enrichment with Compliance mention
    Band-->>Runtime: Delivery status 201
    Runtime->>Queue: Enqueue Compliance dependency update

    Queue-->>Runtime: Forensics work item
    Runtime->>Forensics: Execute Forensics role logic
    Forensics->>Band: Post timeline with Compliance mention
    Band-->>Runtime: Delivery status 201
    Runtime->>Queue: Enqueue Compliance dependency update

    Runtime->>Runtime: Deduplicate Compliance until both upstream roles complete
    Queue-->>Runtime: Compliance work item
    Runtime->>Compliance: Execute Compliance role logic
    Compliance->>Band: Post review with Commander mention
    Band-->>Runtime: Delivery status 201
    Runtime->>Queue: Enqueue Incident Commander

    Queue-->>Runtime: Commander work item
    Runtime->>Commander: Execute final decision logic
    Commander->>Band: Post final Commander decision
    Band-->>Runtime: Delivery status 201
    Runtime->>Runtime: Mark chain complete and stop
    Runtime->>Mission: Write sanitized mission-control-status.json
```

Sequence boundary notes:

- Band provides the shared room, visible posts, mentions, handoffs, and proof surface.
- The backend runtime owns state, sequencing, completion criteria, and fallback behavior.
- Agent-authored Band posts do not need to echo back through Band receive to advance the chain; the in-process handoff queue advances after successful delivery.
- The Commander post is terminal and does not create another workflow handoff.
