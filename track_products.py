import json
import os
import sys
import requests

STATE_FILE = "state.json"
PRODUCTS_FILE = "products.json"

RESEND_API_KEY = os.environ["RESEND_API_KEY"]
NOTIFY_EMAIL = os.environ["NOTIFY_EMAIL"]
# onboarding@resend.dev works with zero setup as long as NOTIFY_EMAIL is the
# same email you used to sign up for Resend. Swap this once you verify a domain.
FROM_EMAIL = os.environ.get("FROM_EMAIL", "onboarding@resend.dev")


def load_json(path, default):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return default


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def fetch_product(url):
    json_url = url.rstrip("/") + ".json"
    resp = requests.get(json_url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
    resp.raise_for_status()
    return resp.json()["product"]


def send_email(subject, body):
    resp = requests.post(
        "https://api.resend.com/emails",
        headers={
            "Authorization": f"Bearer {RESEND_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "from": FROM_EMAIL,
            "to": [NOTIFY_EMAIL],
            "subject": subject,
            "text": body,
        },
        timeout=15,
    )
    if resp.status_code >= 300:
        print(f"Failed to send email: {resp.status_code} {resp.text}", file=sys.stderr)
    else:
        print("Email sent.")


def main():
    products = load_json(PRODUCTS_FILE, [])
    state = load_json(STATE_FILE, {})

    restocks = []

    for url in products:
        try:
            product = fetch_product(url)
        except Exception as e:
            print(f"Error fetching {url}: {e}", file=sys.stderr)
            continue

        title = product.get("title", url)
        variants = product.get("variants", [])

        prev_variants = state.get(url, {})
        new_variants = {}

        for v in variants:
            vid = str(v["id"])
            available = bool(v.get("available"))
            new_variants[vid] = available

            was_available = prev_variants.get(vid)
            # Only alert on a real transition (False -> True), never on the
            # first run when we have no prior state for this variant yet.
            if available and was_available is False:
                restocks.append(f"{title} ({v.get('title', 'default')}) — {url}")

        state[url] = new_variants

    if restocks:
        body = "The following matcha just restocked:\n\n" + "\n".join(restocks)
        send_email("🍵 Matcha restock alert!", body)
        print(body)
    else:
        print("No restocks detected.")

    save_json(STATE_FILE, state)


if __name__ == "__main__":
    main()
