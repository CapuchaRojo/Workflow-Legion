# Sponsor Redemption Checklist

This checklist prevents sponsor credits, access codes, QR codes, private links, API keys, and account-specific credentials from being exposed in the repository or demo video.

## Rule

Do not commit or show private sponsor material.

Sponsor tools may be discussed in the project narrative, but private redemption details must stay outside the repo and outside the recorded demo.

## Never Commit

- [ ] Sponsor redemption codes.
- [ ] Sponsor QR codes.
- [ ] Private redemption URLs.
- [ ] API keys.
- [ ] Band Agent API keys.
- [ ] AI/ML API keys.
- [ ] Featherless API keys.
- [ ] Native.Builder / NativelyAI private workspace links.
- [ ] .env files.
- [ ] Account credentials.
- [ ] Billing screenshots.
- [ ] Private emails or Discord DMs.

## Repo Safety Check

Run before final submission:

git status --short

Confirm:

- [ ] No .env file is staged.
- [ ] No node_modules folder is staged.
- [ ] No dist folder is staged.
- [ ] No build output is staged.
- [ ] No private screenshot is staged.
- [ ] No sponsor code is staged.

Search docs for risky terms:

Select-String -Path docs\*.md -Pattern "api_key","API_KEY","secret","token","Bearer ","sk-","qr","redemption","coupon","code"

Expected result:

- Mentions in safety checklists are allowed.
- Actual keys, codes, QR URLs, private redemption links, and bearer tokens are not allowed.

## Demo Recording Safety

Before recording:

- [ ] Close Gmail.
- [ ] Close Discord DMs.
- [ ] Close sponsor dashboards unless public-safe.
- [ ] Close billing/account pages.
- [ ] Hide bookmarks that reveal private systems.
- [ ] Clear terminal screen before showing commands.
- [ ] Do not open .env.
- [ ] Do not show browser devtools with tokens.
- [ ] Do not show GitHub settings pages containing secrets.

## Sponsor Tool Positioning

Approved language:

- Band is the core collaboration fabric.
- Native.Builder / NativelyAI is the showcase and productization layer.
- AI/ML API is an optional provider support path.
- Featherless is an optional fallback or provider support path.

Avoid:

- Claiming provider APIs are required for the validated proof.
- Claiming Native.Builder coordinates agents.
- Claiming private sponsor access is part of the public repo.
- Showing private sponsor redemption details as proof.

## Final Signoff

- [ ] Repo checked.
- [ ] Docs checked.
- [ ] Screenshots checked.
- [ ] Demo tabs checked.
- [ ] Terminal checked.
- [ ] Submission package checked.

Reviewer:
Date:
