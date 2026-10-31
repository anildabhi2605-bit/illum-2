# AI Provider & Model Manager Specification

## Responsibility

Provide a common request interface, connection/model/capability checks, error normalization, schema validation and usage tracking when exposed. Never implement or reinterpret a skill's prompt/contract inside the provider manager.

## Adapter lifecycle

1. Declare provider adapter and exact supported operations.
2. Validate credentials/connection without exposing secret.
3. Discover models through official API where supported; otherwise use a documented static fallback with last-checked date.
4. Capability metadata: structured output, context limits, tool/browser support, image support, streaming, usage availability — each `Known`, `Unknown` or tested value.
5. Execute request under timeout and provider limits.
6. Normalize error categories and preserve safe details.
7. Validate output schema before returning.
8. Record provider/model, attempt, timestamps and available usage; never record secret.

## Candidate error categories

`MissingConfiguration`, `InvalidCredentials`, `AccessDenied`, `RegionOrPlanRestricted`, `Billing`, `RateLimited`, `QuotaExceeded`, `ModelNotFound`, `Timeout`, `Network`, `ProviderUnavailable`, `InvalidRequest`, `SchemaInvalid`, `UnknownProviderError`.

The implementation may adapt enum names to SDK behavior but must retain distinctions needed for correct retry behavior.

## Routing policy

- Project preferred model takes precedence.
- Only tested adapters/models can be marked Supported.
- On preferred-model failure, explain error and ask explicit permission before alternative model.
- Retry same model only for appropriate transient errors and within configured bound.
- Never blindly retry invalid credentials, access/region/plan, billing or missing-model errors.
- Do not guess cost, quota/reset or capability metadata.
- Validate structured output against each skill's expected schema.

## Minimum first adapter approach

Build provider interface and fake/mock adapter tests first, then one real adapter end-to-end. The first real provider is a P00 decision; Groq is a user-mentioned candidate, not an unconditional assumption that all needed capabilities exist.
