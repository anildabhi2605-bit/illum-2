# Configuration and Secrets Specification

## Requested local key workflow

The user wants a local `.env` file that can be opened in Notepad to add/remove provider API keys. Initial implementation may read `.env` at startup and require restart after edits. Live reload is not assumed.

Example only:

```dotenv
OPENAI_API_KEY=
GEMINI_API_KEY=
GROQ_API_KEY=
OPENROUTER_API_KEY=
DEFAULT_PROVIDER=
DEFAULT_MODEL=
```

Only add keys/variables that are required by implemented adapters. A variable existing in `.env` does not imply its provider is supported.

## Required files and behaviors

- `.env.example`: placeholder keys only, never real values.
- `.env`: local secret file, ignored by Git, permission-restricted where possible.
- `.gitignore`: `.env`, virtual environment, local DB/data, exports, logs, temp files, caches, generated user content.
- App startup validates missing/malformed configuration without printing key values.
- Provider key UI shows configured/not configured and masked state, not full saved key.
- Notepad workflow: edit file → save → restart → validate provider connection.
- Removing a key from `.env` removes local configuration when the app reloads; provider-side revocation requires the provider dashboard.
- Never include `.env` in project export or diagnostic bundle.

## Security trade-off

A local `.env` is usually plain text. It is not AES-GCM encrypted server-side storage. This local mode is an explicit deployment change. The app must document file-access risk, prevent Git commits, redact logs, and recommend immediate provider-side revocation if leaked. Optional OS keyring storage can be considered later for a user-friendly end-user release, but must be a recorded decision, not silently substituted for the requested `.env` flow.

## Secret threat tests

- Search test logs, exported ZIP, generated reports and app errors for test sentinel secrets.
- Verify `.env` is ignored by Git in a clean repository.
- Verify invalid credentials produce sanitized error without printing value.
- Verify key removal followed by restart makes provider unconfigured.
- Verify removing local key does not claim to revoke remote key.
