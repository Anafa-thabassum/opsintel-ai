# Optional LLM Evaluation

## Status

- Evaluation date: **19 October 2026**
- Provider integration: **OpenAI Responses API**
- Configured default model: **`gpt-6-luna`**
- Live model request: **not performed**
- Live usage and cost: **none recorded**

The default model identifier appears in OpenAI's published model catalog, but
this run did not verify that a particular API account can access it. A live
request can incur cost, and no explicit authorization for a billable request
was supplied for this evaluation. Live grounding quality therefore remains
pending. Mocked responses are not presented as evidence of model access.

## Offline method

The focused suite uses synthetic investigations and mocked HTTP responses. It
checks the application boundary around the model rather than model quality.
The model remains disabled by default, and every failure returns an unavailable
optional summary while leaving the deterministic investigation unchanged.

Run the focused checks with:

```bash
.venv/bin/python -m pytest tests/test_llm.py -q
```

Recorded result: **14/14 tests passed**.

| Scenario | Recorded application outcome |
|---|---|
| Feature disabled | No request; deterministic result remains available |
| Missing API key | Optional summary unavailable |
| Structured grounded response | Accepted with exact evidence reference |
| Connection error | Safe deterministic fallback |
| Request timeout | Safe deterministic fallback |
| HTTP 429 rate limit | Safe fallback; key absent from returned error state |
| Malformed JSON | Rejected |
| Incomplete structured response | Rejected |
| Unknown evidence reference | Entire response rejected |
| One ungrounded claim among grounded claims | Entire response rejected |
| Fabricated numeric metric with a valid reference | Entire response rejected |
| Fabricated log claim with a valid reference | Entire response rejected |
| Language claiming a confirmed cause | Entire response rejected |
| Insufficient evidence | Unresolved narrative preserved; cause remains unset |

## Grounding controls

The request uses a strict JSON schema. Each claim must provide one or more
retrieved evidence references and an exact excerpt from every cited
observation. Post-response validation rejects unknown references, excerpts not
present in the cited observations, numeric or run/log identifier tokens absent
from the supplied investigation, and language that claims a confirmed cause or
executed repair. One failed claim rejects the whole optional narrative.

These checks reduce obvious unsupported claims; they do not prove semantic
faithfulness of every paraphrase. A real-model evaluation should therefore
review each statement against its cited observation and record all misses.

## Live evaluation procedure

Only after a user explicitly authorizes possible API cost:

1. Confirm the intended API account can access the configured model.
2. Keep `OPSINTEL_LLM_ENABLED=false` as the default and enable it only for the
   evaluation process.
3. Run representative synthetic incidents, including an unresolved case.
4. Record the provider, exact model ID, case inputs, grounding decisions,
   uncertainty decisions, fallback outcomes, token usage, and reported cost.
5. Do not record the API key or sensitive operational logs.

No claim is made that the optional LLM improves classification accuracy. The
deterministic classifier supplies the category, evidence, candidate causes,
and unconfirmed state whether the model is enabled or not.
