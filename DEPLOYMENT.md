# Deployment

## Streamlit Community Cloud

The repository includes the real survey measurements with participant IDs, a pinned Python environment, the native engine source and `packages.txt` with `g++`. No private CSV or application secret is required for the public interface.

1. Push this repository to GitHub. Keep the identifiable source CSV outside Git; `.gitignore` excludes the original raw and cleaned paths.
2. Sign in at [Streamlit Community Cloud](https://share.streamlit.io/) using the GitHub account that owns the repository. Review the GitHub authorization prompt yourself.
3. Select **Create app**, then **Deploy a public app from GitHub**.
4. Set repository to `ashrith-r/casper-roommate`, branch to `main`, and main file to `NITW_Roommate_Optimizer/app.py`.
5. Open **Advanced settings** and select Python **3.12**. Choose an available app subdomain.
6. Leave secrets empty for the public matching application. Optional administrator features are described below.
7. Select **Deploy**. The service installs the Python dependencies and `g++`; the application builds the C++ engine on its first execution.
8. Check that Overview shows 98 participants, that Pair explorer renders its radar and that Benchmarks shows computed results. Change λ, select Run CASPER and confirm the allocation refreshes.
9. Put the resulting `https://…streamlit.app` address in the GitHub repository's About → Website field. Future pushes to the selected branch update the deployment.

The [official deployment guide](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy) explains the current form. The [dependency guide](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/app-dependencies) covers `requirements.txt` and Debian packages in `packages.txt`.

GitHub Pages cannot run Python or C++. If the repository previously hosted a static version, unpublish it under Settings → Pages so visitors use the Streamlit deployment.

## Optional administrator features

Add these keys in the app's Streamlit **Settings → Secrets** only when needed:

| Key | Purpose |
| --- | --- |
| `CASPER_ADMIN_PASSWORD` | A strong password you create for private uploads and notifications |
| `EMAIL_USER` | Actual SMTP login/address |
| `EMAIL_PASS` | SMTP application password from your email provider |
| `SMTP_HOST` | Optional SMTP host; default `smtp.gmail.com` |
| `SMTP_PORT` | Optional TLS port; default `465` |

Use quoted TOML strings. Do not commit values or paste credentials into issues, documentation or chat. Locally, use `.streamlit/secrets.toml` in the repository root, which Git ignores. There are no default administrator credentials.

Sign in through the sidebar, then use Survey evidence to load the private source into that session. Public files contain no email addresses. Uploading to the hosted app transfers the CSV to Streamlit's server; use a local administrator session if the source must remain entirely on your computer. Signing out restores the public dataset. Room assignments require actual room IDs; none are generated.

Notifications require a reviewed pairing, both addresses, configured SMTP and explicit confirmation in the app. Delivery is not atomic: one recipient can succeed before the other fails. Successful recipients are tracked within the current session to avoid duplicate retries; this is not a durable delivery log across restarts. No email is sent by tests or normal deployment.

## Local setup

Use Python 3.12. Install a C++17 compiler from your platform's official toolchain package. On Debian/Ubuntu, `sudo apt-get install g++`. On Windows, a GCC distribution such as [w64devkit](https://github.com/skeeto/w64devkit) provides `g++.exe`; put its `bin` folder on PATH or set `CXX` to the executable path.

From the repository root:

```sh
python -m venv .venv
```

Activate with `.venv\Scripts\Activate.ps1` in PowerShell, or `source .venv/bin/activate` in a POSIX shell. If PowerShell activation is restricted, call `.venv\Scripts\python.exe` directly instead of changing machine-wide policy.

```sh
python -m pip install -r requirements.txt
python -m streamlit run NITW_Roommate_Optimizer/app.py
```

Run from the repository root so Streamlit reads `.streamlit/config.toml`. The C++ binary is compiled from source into an ignored build folder. `CASPER_BUILD_DIR` can select a writable cache directory on hosts where the source checkout is read-only.

## Command-line allocation

```sh
cd NITW_Roommate_Optimizer
python -m src.main --lambda 0.5 --threshold 0.4 --output allocation.csv
```

This uses the public real measurements by default. Use `--data` with a local private source if needed. Exports contain participant IDs and include unmatched participants.

## Optional FastAPI service

The retained API is a separate process; Community Cloud hosts the Streamlit application, not an additional publicly exposed FastAPI server. The online Streamlit screen uses the shared pipeline directly.

Configure `CASPER_API_KEY` as a strong server environment secret, then run from `NITW_Roommate_Optimizer`:

```sh
python -m uvicorn src.realtime.api:app --host 127.0.0.1 --port 8000
```

`GET /health` reports availability. `POST /run_matching/` requires `X-API-Key`; its JSON body contains `records`, optional `lambda_`, `threshold`, `max_sweeps` and `preserve_pairs`. Use `/docs` locally for the schema. It is stateless: clients provide the full current dataset and any preserved ID pairs. Deploy behind HTTPS and application-level access controls if exposing this optional service beyond localhost.

## Troubleshooting

| Symptom | Resolution |
| --- | --- |
| Compiler unavailable | Check `g++` on PATH, `CXX`, and root `packages.txt`; reboot the cloud app after dependency changes |
| App build fails | Confirm Python 3.12, repository branch and main-file path; inspect the Streamlit build log |
| Public dataset unavailable | Ensure `data/processed/participants.csv` is committed; no raw CSV is needed |
| Upload rejected | Read the column/row validation message; numeric features require 0–10 and interests require the original field or six binary indicators |
| Some participants unmatched | Inspect exclusions and threshold; the matcher never silently bypasses constraints |
| Export disabled | Run CASPER after changing settings so exports correspond to the displayed settings |
| Online entries disappear | Sessions are temporary; download the allocation before leaving and retain new source responses privately |
| SMTP disabled | Configure administrator and SMTP secrets, sign in, and load real recipient addresses |

The cloud service can suspend inactive apps. Cold starts include dependency/application startup and may rebuild the native binary. This project makes no uptime guarantee.
