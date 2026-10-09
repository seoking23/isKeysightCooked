# isKeysightCooked

"Who Is Teaching the Next Engineer?" is a digital presence audit of Keysight vs. Rohde & Schwarz, NI and Tektronix (data captured Oct 1, 2026), published as a single encrypted page.

**Internal proposal by Douglas Seo and Nidhi Sundkam. Not an official Keysight Technologies publication.** Trademarks belong to their respective owners. Do not redistribute outside Keysight without Marketing and Legal review.

## How it works

- `index.html` is a public shell: styles, a two-step gate and the decrypt script. The post itself is **not** in this repo.
- On every push to `main`, `.github/workflows/deploy.yml` runs `.github/encrypt.py`. It encrypts the post in two layers and deploys the result to GitHub Pages: the question answer (check 1) opens the outer layer, and the access code (check 2) opens the post.
- Encryption, per layer: PBKDF2-SHA256 (600k iterations, random salt) → AES-256-CBC + HMAC-SHA256. The answer isn't case-sensitive; the code is. The browser decrypts with WebCrypto.

## Repository secrets

| Secret | Contents |
|---|---|
| `PAGE_PASSWORD` | Check 1: the answer to the gate question |
| `PAGE_CODE` | Check 2: the access code |
| `POST_HTML_GZ` | The post HTML, gzipped then base64-encoded |
| `GEMINI_PNG` | The Gemini screenshot, base64-encoded |

## Editing the post

The plaintext source lives outside the repo in `_private/` (`post.html`, `gemini-answer.png`). Keep a backup somewhere private. After editing:

```bash
gzip -9c _private/post.html | base64 | gh secret set POST_HTML_GZ
gh workflow run deploy.yml
```

Local preview with a throwaway answer: `PAGE_PASSWORD=test PAGE_CODE=test2 python3 .github/encrypt.py _private/_site`, then serve `_private/_site`.
