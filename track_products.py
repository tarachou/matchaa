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

HEADERS = {"User-Agent": "Mozilla/5.0"}


def load_json(path, default):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return default


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


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


def check_shopify(url):
    """Shopify stores expose a clean .json endpoint per product."""
    json_url = url.rstrip("/") + ".json"
    resp = requests.get(json_url, timeout=15, headers=HEADERS)
    resp.raise_for_status()
    product = resp.json()["product"]
    title = product.get("title", url)
    variants = {str(v["id"]): bool(v.get("available")) for v in product.get("variants", [])}
    return title, variants


def check_html_text(url, out_of_stock_text):
    """For non-Shopify sites: available unless a known 'sold out' phrase is on the page."""
    resp = requests.get(url, timeout=15, headers=HEADERS)
    resp.raise_for_status()
    is_out_of_stock = out_of_stock_text.lower() in resp.text.lower()
    return url, {"default": not is_out_of_stock}


def main():
    products = load_json(PRODUCTS_FILE, [])
    state = load_json(STATE_FILE, {})

    restocks = []

    for entry in products:
        # Old entries are plain Shopify URL strings; new entries are dicts
        # with a "type" so we know how to check them.
        if isinstance(entry, str):
            entry = {"type": "shopify", "url": entry}

        url = entry["url"]
        ptype = entry.get("type", "shopify")

        try:
            if ptype == "shopify":
                title, variants = check_shopify(url)
            elif ptype == "html":
                title, variants = check_html_text(url, entry["out_of_stock_text"])
            else:
                print(f"Unknown product type '{ptype}' for {url}", file=sys.stderr)
                continue
        except Exception as e:
            print(f"Error checking {url}: {e}", file=sys.stderr)
            continue

        prev_variants = state.get(url, {})

        for vid, available in variants.items():
            was_available = prev_variants.get(vid)
            # Only alert on a real transition (False -> True), never on the
            # first run when we have no prior state for this item yet.
            if available and was_available is False:
                label = "" if vid == "default" else f" ({vid})"
                restocks.append(f"{title}{label} — {url}")

        state[url] = variants

    if restocks:
        body = "The following matcha just restocked:\n\n" + "\n".join(restocks)
        send_email("🍵 Matcha restock alert!", body)
        print(body)
    else:
        print("No restocks detected.")

    save_json(STATE_FILE, state)


if __name__ == "__main__":
    main()
