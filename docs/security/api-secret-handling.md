# API Secret Handling (Preferred)

Use environment variables for API keys whenever possible. This avoids writing plaintext keys into files that could be accidentally committed.

## Preferred order

1. **Environment variables** (recommended)
   - `OPENAI_API_KEY`
   - `GOOGLE_API_KEY`
   - `DEEPSEEK_API_KEY`
2. **Local `.env` file** loaded by your shell/tooling and ignored by git.
3. **OS keyring / secret manager** (Keychain, Credential Manager, libsecret, cloud secret stores) where available.
4. **Local fallback file** `config/pygpt_net/config.json` only when necessary.

## Local fallback file warnings

- Treat `config/pygpt_net/config.json` as **local-only**.
- Keep it gitignored (this repository already ignores that path).
- Restrict file permissions (`chmod 600`) when supported.
- Never print API key values in logs or prompts.
- Do not save empty placeholder values as configuration.
