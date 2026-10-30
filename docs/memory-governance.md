# Memory governance

- **Submission:** only a configured engineer actor can submit source-backed evidence. The packet is pending and cannot set a confirmed cause.
- **Approval:** a different configured reviewer must attest every versioned criterion with a method, result, and source reference. The API rejects missing causal evidence, unresolved classifier conflicts, incomplete criteria, or self-approval. The reviewer is responsible for verifying external source authenticity and relevance.
- **Correction:** a new reviewed submission replaces current fields only after approval. The prior version is retained in `INCIDENT_AUDIT`, revision increments, and old matches become stale.
- **Revocation:** a reviewer gives a recorded rationale; revoked records are excluded from future matching. Audit history remains.
- **Candidate rejection:** an engineer may reject a retrieval result for a run. This does not revoke the historical confirmed incident.
- **Privacy:** use pseudonymous actor IDs, store only the necessary source excerpt, and avoid secret-bearing log text. All memory API reads require a token. Exasol credentials and bearer grants belong in a secret manager. The application does not fetch arbitrary URLs or send memory content to the optional LLM.

The reviewer checklist is a control on the confirmation workflow, **not empirical validation** of the seven category policies. Review real cases and update criteria through a new version when evidence shows a flaw. The initial release has no automatic retention or deletion policy, no enterprise SSO, and no full production audit of access to read endpoints.
