# Incident fingerprinting

Version `word-pairs-v1` lowercases log observations and removes variable timestamps, UUIDs, run/request IDs, paths, and standalone numbers. It retains SQLSTATE/ORA-style error codes, field names, and diagnostic words. The token set contains individual words and adjacent word pairs. Structured features include supported symptom category, completeness band, upstream state when present, and error codes.

Jaccard similarity over token sets contributes 70% of the score and structured-feature agreement contributes 30%. Contradictory category, error-code, and other shared features reduce the score. Different supported symptom categories are ineligible. `OPSINTEL_MEMORY_MIN_SIMILARITY` sets a threshold from 0 to 1; it defaults to `0.42`. The score is **not** a probability of causal correctness. The threshold is a development choice and has not been calibrated on an independent memory benchmark because no confirmed-cause query set is available.

Exasol stores the versioned fingerprint and features and filters active, non-self candidates. The application computes Jaccard because the current schema stores token sets as JSON and a small bounded scan is simpler to audit than a database token-pair join. At more than 500 active records, Exasol returns the 500 most recently confirmed candidates; this recency cap can miss older relevant incidents. If measured scale requires it, add a token index table and database-side prefiltering. Do not silently change the version for existing records.

Matching and differing features are returned separately. A historical confirmed cause is always presented as a candidate for the new run. Correction stales prior matches; revocation removes the record from retrieval.
