# Publish CASPER on GitHub Pages

Target repository: **ashrith-r/casper-roommate**  
Expected Pages address after deployment: **https://ashrith-r.github.io/casper-roommate/**

## First deployment through GitHub

1. Sign in as **ashrith-r**, then create a repository named **casper-roommate**. A public repository supports Pages on GitHub Free. Use the description: “An explainable roommate matching studio — a design-thinking project reimagined by ASHRITH RAJU.”
2. Upload the project contents with the folder structure preserved. The repository root must contain `README.md`, `package.json`, `site/`, `scripts/`, `tests/` and `.github/workflows/pages.yml`. Do not upload the containing folder or the source ZIP as a replacement for these files.
3. Commit to **main**.
4. Open the repository’s **Settings → Pages → Build and deployment → Source** and select **GitHub Actions**.
5. Open **Actions → Test and deploy CASPER → Run workflow**, choose **main**, and run it. If a prior push started a failed run before Pages was enabled, rerun after step 4.
6. Wait for the deployment job to turn green. Open its **github-pages** environment URL or the address above.
7. Try **Why this match**, change the penalty and choose **Update matches**, then import `site/template.csv` from the Students view and export a report.

The workflow tests the model and uploads only `site/`. Project documents, tests, and scripts remain in the repository but are not part of the website artifact.

## Command-line alternative

Install [Git](https://git-scm.com/downloads), [GitHub CLI](https://cli.github.com/) and [Node.js](https://nodejs.org/). In the downloaded project folder:

```sh
node --test tests/*.test.mjs
git init -b main
git add .
git commit -m "Build CASPER roommate matching studio"
gh auth login
gh repo create ashrith-r/casper-roommate --public --source=. --remote=origin --push
```

Run `gh repo create` only if that repository does not already exist. If the repository is already created, clone it and copy your changes into the clone instead. Never force-push over existing work. Enable Pages from Settings as described above.

Do not paste passwords or tokens into chat, code, or Git remote URLs. Complete GitHub authentication through the official login flow.

## Update after deployment

```sh
git clone https://github.com/ashrith-r/casper-roommate.git
cd casper-roommate
node scripts/serve.mjs
```

Edit the files, preview at http://127.0.0.1:4173, stop the preview with Ctrl+C, then:

```sh
node --test tests/*.test.mjs
git add .
git commit -m "Describe your change"
git push
```

Every push to main tests and redeploys the site. No hosting keys or package installation are needed.

## A strong project presentation

1. Pin the repository on your profile and add the live URL to the repository’s About section.
2. Use the fictional demo for public screenshots. Show the studio, one match explanation and the method page.
3. Explain the problem and survey process, demonstrate a changed conflict setting, and show why individual pairs changed.
4. Describe this as your **redesign and implementation of a group project**. Add confirmed teammates in `CREDITS.md`.
5. Discuss limitations openly: the heuristic is not exact matching, the weights need validation, and suggestions require human review.

## Troubleshooting

- **Pages 404:** confirm the green deployment completed, Pages uses GitHub Actions, and the URL includes `/casper-roommate/`.
- **“Get Pages site failed”:** enable Pages in repository Settings, then rerun the workflow.
- **Blank app:** open the hosted URL or the local HTTP server, not a `file://` URL; inspect the browser console for missing module paths.
- **CSV scale error:** select 0–10 for original survey rows, or 0–1 for normalized columns. Required missing values are not filled automatically.
- **Too few pairs:** inspect excluded connections, the cohort size and conflict threshold; greedy matching does not guarantee the maximum possible pair count.

Official guidance: [GitHub Pages custom workflows](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages).
