# Natively Source Export Audit

## Context

Natively / Native.Builder GitHub Sync was still failing for this workspace, but the builder provided a Download source code option in the bottom-right of the screen.

The exported source code was saved outside this repository at:

C:\Users\mich3\GitHubProjects\Workflow-Legion--Cyber-Incident-Command-Room-source-code

This audit records the local validation result without importing the generated source into the main Workflow Legion repository.

## Validation Performed

From the exported Natively source folder, these commands were run:

cd C:\Users\mich3\GitHubProjects\Workflow-Legion--Cyber-Incident-Command-Room-source-code
npm install
npm run build

## Result

npm install completed successfully.

NPM reported:

2 high severity vulnerabilities

No automatic fix was applied. npm audit fix --force was intentionally not run because it may introduce breaking dependency changes.

npm run build completed successfully:

vite v7.3.5 building client environment for production...
1764 modules transformed.
dist/index.html                   0.50 kB gzip: 0.33 kB
dist/assets/index-B8LjnsOr.css   50.99 kB gzip: 8.26 kB
dist/assets/index-fOA66WAZ.js   224.54 kB gzip: 63.92 kB
built in 2.71s

## Safety Notes

The export remains outside the main repository for now.

Do not commit:

- node_modules/
- dist/
- raw build output
- .env files
- API keys
- sponsor codes
- private credentials
- redemption links
- QR codes

The current merged frontend-showcase/ remains the validated showcase path for the hackathon submission. This Natively export is treated as a backup/proof artifact and future comparison source, not as a replacement.

## Follow-up Options

Potential future work:

1. Compare the Natively export against frontend-showcase/.
2. Import only selected UI improvements if they improve the final demo.
3. Remove or avoid committing Natively-specific runtime bridge files unless explicitly needed.
4. Replace remote font loading with system fonts if source is merged into the repo.
5. Re-run dependency audit before any generated source is committed.
