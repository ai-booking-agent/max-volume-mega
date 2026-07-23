import requests

from . import config

API_VERSION = "v21.0"
API_BASE = f"https://graph.facebook.com/{API_VERSION}"

TEMPLATE_NAME = "max_volume_mega_screenshot"
TEMPLATE_LANGUAGE = "en_US"


def _headers():
    return {"Authorization": f"Bearer {config.WHATSAPP_ACCESS_TOKEN}"}


def _require_config():
    if not (
        config.WHATSAPP_ACCESS_TOKEN
        and config.WHATSAPP_PHONE_NUMBER_ID
        and config.WHATSAPP_RECIPIENT_NUMBER
    ):
        raise RuntimeError(
            "WHATSAPP_ACCESS_TOKEN, WHATSAPP_PHONE_NUMBER_ID, and WHATSAPP_RECIPIENT_NUMBER "
            "must all be set in .env"
        )


def _upload_media(image_path):
    url = f"{API_BASE}/{config.WHATSAPP_PHONE_NUMBER_ID}/media"
    with open(image_path, "rb") as f:
        resp = requests.post(
            url,
            headers=_headers(),
            data={"messaging_product": "whatsapp", "type": "image/png"},
            files={"file": (image_path.name, f, "image/png")},
            timeout=30,
        )
    if not resp.ok:
        raise RuntimeError(f"WhatsApp media upload failed: {resp.status_code} {resp.text}")
    return resp.json()["id"]


def _send(payload):
    url = f"{API_BASE}/{config.WHATSAPP_PHONE_NUMBER_ID}/messages"
    resp = requests.post(url, headers=_headers(), json=payload, timeout=30)
    if not resp.ok:
        raise RuntimeError(f"WhatsApp send failed: {resp.status_code} {resp.text}")
    return resp.json()


def send_freeform(image_path, caption):
    """Free-form image message. Only delivers if the recipient has messaged
    this WhatsApp number within the last 24 hours (WhatsApp platform rule)."""
    _require_config()
    media_id = _upload_media(image_path)
    return _send(
        {
            "messaging_product": "whatsapp",
            "to": config.WHATSAPP_RECIPIENT_NUMBER,
            "type": "image",
            "image": {"id": media_id, "caption": caption},
        }
    )


def send_via_template(image_path, date_text):
    """Approved-template image message. Delivers any time, no 24h window
    requirement — this is what the daily unattended job should use.
    Requires the 'max_volume_mega_screenshot' template to be approved."""
    _require_config()
    media_id = _upload_media(image_path)
    return _send(
        {
            "messaging_product": "whatsapp",
            "to": config.WHATSAPP_RECIPIENT_NUMBER,
            "type": "template",
            "template": {
                "name": TEMPLATE_NAME,
                "language": {"code": TEMPLATE_LANGUAGE},
                "components": [
                    {
                        "type": "header",
                        "parameters": [{"type": "image", "image": {"id": media_id}}],
                    },
                    {
                        "type": "body",
                        "parameters": [{"type": "text", "text": date_text}],
                    },
                ],
            },
        }
    )


def send_screenshot(image_path, date_text, caption=None):
    """Tries the approved template first (works any time); falls back to a
    free-form message (only works within the 24h window) if the template
    isn't approved yet or fails for some other reason."""
    try:
        return send_via_template(image_path, date_text)
    except Exception as exc:
        import logging

        logging.getLogger("max-volume-mega").warning(
            "WhatsApp template send failed (%s), falling back to free-form", exc
        )
        return send_freeform(image_path, caption or date_text)
