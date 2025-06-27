import logging
import json
import requests
from typing import Dict, Any, Optional
from django.core.cache import cache
from django.http.request import (
    HttpHeaders
)
from .models import RoutingRule, Environment

logger = logging.getLogger(__name__)


def get_wa_id_from_payload(payload: Dict[str, Any]) -> Optional[str]:
    try:
        return payload["entry"][0]["changes"][0]["value"]["messages"][0]["from"]
    except (KeyError, IndexError):
        return None


def process_and_forward_request(
    vendor_code: str, payload: Dict[str, Any], headers: HttpHeaders
) -> Optional[requests.Response]:
    wa_id = get_wa_id_from_payload(payload)
    if not wa_id:
        logger.warning(
            f"Could not extract wa_id from payload for vendor '{vendor_code}'."
        )
        return None

    cache_key = f"rule:{vendor_code}:{wa_id}"
    cached_rule = cache.get(cache_key)

    if cached_rule:
        target_url = cached_rule["target_url"]
        secure_vars = cached_rule["secure_variables"]
    else:
        try:
            rule = RoutingRule.objects.select_related("environment__vendor").get(
                wa_id=wa_id, environment__vendor__code=vendor_code
            )
            target_url = rule.environment.target_url
            secure_vars = rule.environment.vendor.secure_variables
        except RoutingRule.DoesNotExist:
            try:
                default_env = Environment.objects.select_related("vendor").get(
                    vendor__code=vendor_code, is_default=True
                )
                target_url = default_env.target_url
                secure_vars = default_env.vendor.secure_variables
            except Environment.DoesNotExist:
                logger.error(
                    f"No routing rule or default environment found for vendor '{vendor_code}' and wa_id '{wa_id}'."
                )
                return None

        cache.set(
            cache_key, {"target_url": target_url, "secure_variables": secure_vars}
        )

    forwarding_headers = {
        "Content-Type": "application/json",
        "User-Agent": "W-Router/1.0",
    }

    if secure_vars:
        try:
            decrypted_vars = json.loads(secure_vars)
            if isinstance(decrypted_vars, dict):
                forwarding_headers.update(decrypted_vars)
        except (json.JSONDecodeError, TypeError):
            logger.error(
                f"Could not parse secure_variables for vendor '{vendor_code}'."
            )

    try:
        response = requests.post(
            target_url,
            data=json.dumps(payload),
            headers=forwarding_headers,
            timeout=10,
        )
        response.raise_for_status()
        return response
    except requests.exceptions.RequestException as e:
        logger.error(
            f"Failed to forward request for vendor '{vendor_code}' to {target_url}. Error: {e}"
        )
        return None
