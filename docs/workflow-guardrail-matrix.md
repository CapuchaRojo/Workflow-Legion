# Workflow Legion Guardrail Matrix

## Purpose

This document maps Track 3 (Regulated & High-Stakes Workflows) requirements to Workflow Legion controls. The objective is to demonstrate how review, traceability, escalation, deterministic execution, and safe reporting are preserved throughout the incident response workflow.

## Operating Principles

### Collaboration Fabric and Proof Surface

Band serves as the collaboration fabric and proof surface. Agent activity, handoffs, mentions, and workflow progression remain visible for review and auditability.

### Deterministic Runtime

The backend serves as the deterministic workflow runtime. State transitions, routing decisions, and workflow progression are governed by predictable runtime behavior rather than hidden autonomous reasoning.

### Sanitized Visibility

Mission Control provides sanitized operational visibility suitable for demonstrations and reporting. Sensitive operational details are excluded from exported views.

### Provider Independence

AI/ML API and Featherless function as optional provider support layers. Workflow integrity does not depend on a single provider implementation.

## Track 3 Guardrail Matrix

| Requirement/Risk Area | Potential Risk | Workflow Legion Control | Outcome |
|-----------------------|----------------|-------------------------|---------|
| Visible collaboration trail | Investigation activity cannot be reviewed or validated | Band-Visible Proof | Reviewable and auditable workflow progression |
| Grounded agent responsibilities | Agents generate overlapping or unstructured outputs | Grounded Role Outputs | Clear ownership and role-specific contributions |
| Deterministic workflow execution | Runtime behavior varies between demonstrations | Deterministic Backend State | Consistent and reproducible workflow execution |
| Escalation governance | Critical incidents lack a defined decision path | Explicit Escalation | Structured progression toward decision authority |
| Compliance awareness | Regulatory or audit concerns are overlooked | Compliance Caution | Compliance implications are surfaced before action |
| Controlled workflow completion | Investigations continue without closure criteria | Commander Stop Condition | Clear workflow termination and final recommendation |
| Safe reporting | Operational details appear in demonstration artifacts | Sanitized Mission Control Reporting | Demonstration-safe visibility and reporting |
| Provider resilience | Provider interruption affects workflow continuity | Provider Fallback | Reduced dependency on a single provider |
| Credential protection | Sensitive information is exposed during development or demonstration | No-Secret Policy | Secure handling of operational credentials and identifiers |

## Role-Based Control Model

### Alert Triage Agent

Establishes the incident frame, validates incoming activity, and initiates workflow routing.

### Threat Intelligence Agent

Provides indicator enrichment, contextual intelligence, and investigative direction.

### Forensics Agent

Builds evidence timelines, identifies investigation gaps, and maintains investigative context.

### Compliance Agent

Introduces audit, escalation, reporting, and governance considerations. Workflow Legion surfaces governance and compliance context for review, but it does not provide legal advice or final regulatory determinations.

### Incident Commander Agent

Reviews accumulated context, issues containment recommendations, and enforces workflow termination conditions.

## Demonstration Assurance

Workflow Legion is designed for regulated cybersecurity investigation workflows where visibility, reviewability, escalation, and traceability are mandatory.

The system emphasizes:

1. Visible collaboration through Band
2. Deterministic backend workflow execution
3. Explicit escalation and decision ownership
4. Compliance-aware investigation processes
5. Sanitized reporting for demonstrations and review
6. Protection of operational credentials and sensitive information

