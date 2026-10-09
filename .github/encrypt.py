"""Encrypt the post into index.html and write the deployable site.

Usage:  python3 .github/encrypt.py OUT_DIR
Env:    PAGE_PASSWORD  check 1: the answer to the gate question (case-insensitive)
        PAGE_CODE      check 2: the access code (case-sensitive)
        POST_HTML_GZ   gzipped + base64 post HTML (CI); falls back to _private/post.html
        GEMINI_PNG     base64 screenshot (CI); falls back to _private/gemini-answer.png

Scheme: two layers, each PBKDF2-SHA256 (random 16-byte salt) -> AES-256-CBC + HMAC-SHA256,
encrypt-then-MAC. The code seals the post; the answer seals that inner payload.
Standard library plus the system `openssl` binary only.
"""
import base64, gzip, hashlib, hmac, json, os, pathlib, re, shutil, subprocess, sys

ITER = 600_000
ROOT = pathlib.Path(__file__).resolve().parent.parent
out = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "_site")

answer = os.environ.get("PAGE_PASSWORD", "").strip().lower()
code = os.environ.get("PAGE_CODE", "").strip()
if not answer:
    sys.exit("PAGE_PASSWORD is not set")
if not code:
    sys.exit("PAGE_CODE is not set")

if os.environ.get("POST_HTML_GZ"):
    post = gzip.decompress(base64.b64decode(os.environ["POST_HTML_GZ"])).decode()
    png = os.environ.get("GEMINI_PNG", "").strip()
else:
    post = (ROOT / "_private/post.html").read_text()
    png = base64.b64encode((ROOT / "_private/gemini-answer.png").read_bytes()).decode()
if not png:
    sys.exit("GEMINI_PNG is not set")
post = post.replace("{{GEMINI_PNG}}", "data:image/png;base64," + png)

enc = lambda b: base64.b64encode(b).decode()


def seal(secret, data):
    salt, iv = os.urandom(16), os.urandom(16)
    keys = hashlib.pbkdf2_hmac("sha256", secret.encode(), salt, ITER, 64)
    ct = subprocess.run(
        ["openssl", "enc", "-aes-256-cbc", "-K", keys[:32].hex(), "-iv", iv.hex()],
        input=data, capture_output=True, check=True,
    ).stdout
    tag = hmac.new(keys[32:], iv + ct, hashlib.sha256).digest()
    return {"iter": ITER, "salt": enc(salt), "iv": enc(iv), "ct": enc(ct), "tag": enc(tag)}


inner = seal(code, post.encode())
payload = json.dumps(seal(answer, json.dumps(inner).encode()))

page = (ROOT / "index.html").read_text()
page, n = re.subn(r'(<script id="payload" type="application/json">).*?(</script>)',
                  lambda m: m.group(1) + payload + m.group(2), page, flags=re.S)
if n != 1:
    sys.exit("payload placeholder not found in index.html")

if out.exists():
    shutil.rmtree(out)
out.mkdir(parents=True)
(out / "index.html").write_text(page)
shutil.copytree(ROOT / "assets", out / "assets")
if (ROOT / "data.json").exists():
    shutil.copy(ROOT / "data.json", out / "data.json")
print(f"wrote {out}/index.html ({len(page) // 1024} KB)")
