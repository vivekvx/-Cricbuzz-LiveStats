# Streamlit Community Cloud deployment

Prepared on 24 October 2026. This document prepares deployment; it does not claim an app has already been published.

## Exact deployment values

| Field | Value |
|---|---|
| Repository | `vivekvx/-Cricbuzz-LiveStats` |
| Branch | `main` |
| Main file path | `main.py` |
| Python version in Advanced settings | **3.11** |
| Python dependencies | root `requirements.txt` |
| Streamlit configuration | `.streamlit/config.toml` |
| Secrets template | `.streamlit/secrets.toml.example` |
| System packages | None required for the app |

The repository root contains the entry point and requirements. Community Cloud runs from the repository root, so page imports, SQL files and documentation paths resolve without local absolute paths. The optional video recorder uses local Chrome/FFmpeg and is not invoked by the hosted app. Test, lint and recording tools are excluded from runtime requirements and remain in requirements-dev.txt.

## Deploy

1. Open [Streamlit Community Cloud](https://share.streamlit.io/) and sign in with the GitHub account that can access the repository.
2. Choose **Create app**, select the repository/branch/main file above. Enter the values manually if the picker does not list the repository.
3. Open **Advanced settings**, select Python **3.11**, and paste this TOML into **Secrets**, filling the key privately:

```toml
RAPIDAPI_KEY = "YOUR_ACTUAL_RAPIDAPI_KEY"
DEPLOYMENT_ENV = "community-cloud"
```

The existing local `.env` has the configured key. It is intentionally excluded from GitHub, and will not be copied automatically to Streamlit. Do not paste it into a source file or GitHub issue. Sample mode works if RAPIDAPI_KEY is empty; Live API clearly reports the missing key.

4. Save Advanced settings, choose an available app subdomain and deploy. Wait for the build logs to report a running app. No manual database initialization or API polling task is necessary.
5. Review app sharing/access settings and keep the assignment demo private to its intended viewers. All viewers otherwise share the CRUD data and configured API quota; no app-level authentication is added by this project.

## Storage behavior

The app creates sample.sqlite3 and live.sqlite3 at startup under data/, keeping sample and provider data separate. The first-use sample seed is serialized so simultaneous visitors cannot insert duplicate fixtures. No generated databases or personal records are shipped in GitHub.

Community Cloud does **not guarantee persistence of local files**. A restart, rebuild or platform cleanup can remove SQLite edits and cached live data. The deterministic sample data can be recreated; fetch live snapshots again explicitly. Use CSV export to retain results. The sidebar displays this shared/temporary storage behavior when DEPLOYMENT_ENV is community-cloud.

For an academic demonstration, temporary SQLite storage is suitable and preserves the assignment's minimal architecture. Durable production CRUD would require an external persistent database or another hosting arrangement; this preparation does not claim to provide that.

## Post-deployment checks

- Home loads with 60 synthetic fixtures, eight players and 25 questions on first startup.
- All four module links load and the hosted-storage notice is visible.
- Execute Q1, Q12, Q16, Q23 and Q25 in Sample Data; export one CSV.
- Create a uniquely named demonstration player, read and update it, then confirm deletion.
- Choose Live API and press Refresh matches once; confirm an API fetch timestamp and provider records. Choose an available match and fetch its scorecard. No sample fallback should occur on an API failure.
- Fetch a player profile/career table by provider ID if quota permits. Never expose the key in screenshots.
- Check build/runtime logs for errors. Reboot once if desired, understanding that local records can reset.

## Verification before publishing

The GitHub Actions workflow in `.github/workflows/ci.yml` checks Python 3.11 on Ubuntu, pinned dependencies, all tests, code formatting and dependency compatibility without using the live key or network API calls. Local tests also cover Cloud-secrets loading, hosted-storage disclosure and six simultaneous first visitors.

No runtime.txt, Dockerfile or packages.txt is needed. Python is selected explicitly in the deployment UI, following Streamlit's documented workflow.

## Common deployment problems

- **Wrong Python:** choose 3.11 in Advanced settings; do not rely on the platform default.
- **Missing key:** put RAPIDAPI_KEY at the TOML root in Cloud Secrets, then restart if prompted.
- **Bad TOML:** quote the key and deployment environment; do not paste dotenv `KEY=value` syntax.
- **Build installs browser tooling:** ensure Community Cloud is using root requirements.txt, not requirements-dev.txt.
- **Empty Live API after reboot:** local snapshots may have reset; use manual refresh and scorecard fetch.
- **Database edits disappeared:** local storage is temporary; use exports or plan persistent storage.
- **Unexpected API limits:** all viewers use the same provider subscription; keep the demo private and refresh only when needed.

## Official references checked

- [Deployment and Python selection](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy)
- [Dependency declarations](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/app-dependencies)
- [Repository file organization](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/file-organization)
- [Cloud secrets management](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/secrets-management)
- [Local file persistence limitation](https://docs.streamlit.io/develop/concepts/connections/connecting-to-data)
