import logging
import json
import requests
from typing import Dict, Any, Optional
from django.core.cache import cache
from django.http.request import (
    HttpHeaders
)

from wa_router.utils.logging_utils import log_object
from .models import ProcessedMessage, RoutingRule, Environment

logger = logging.getLogger("router")

def get_message_id_from_payload(payload: Dict[str, Any]) -> Optional[str]:
    try:
        return payload["entry"][0]["changes"][0]["value"]["messages"][0]["id"]
    except (KeyError, IndexError):
        return None


def get_wa_id_from_payload(payload: Dict[str, Any]) -> Optional[str]:
    try:
        wa_id = payload["entry"][0]["changes"][0]["value"]["messages"][0]["from"]
        logger.info(f"✅ Successfully extracted wa_id: {wa_id}")
        return wa_id
    except (KeyError, IndexError):
        return None


def process_and_forward_request(
    vendor_code: str, payload: Dict[str, Any], headers: HttpHeaders
) -> Optional[requests.Response]:
    message_id = get_message_id_from_payload(payload)
    if not message_id:
        return None
    
    if ProcessedMessage.objects.filter(meta_id=message_id).exists():
        logger.info(f"🔄 DUPLICATE MESSAGE - Skipping already processed message {message_id}")
        return None
    
    
    wa_id = get_wa_id_from_payload(payload)
    if not wa_id:
        return None
    
    try:
        ProcessedMessage.objects.create(
            meta_id=message_id,
            vendor_code=vendor_code,
            wa_id=wa_id
        )
        logger.info(f"📋 Recorded new message {message_id} from {wa_id}")
    except Exception as e:
        logger.error(f"⚠️  Failed to record message {message_id}: {e}")
        

    cache_key = f"rule:{vendor_code}:{wa_id}"
    cached_rule = cache.get(cache_key)

    if cached_rule:
        target_url = cached_rule["target_url"]
        env_name = cached_rule["env_name"]
        env_code = cached_rule["env_code"]
        secure_vars = cached_rule["secure_variables"]
        logger.info(f"⚡ Cache HIT - Using cached routing rule for {vendor_code} {env_name}({env_code}):{wa_id} to {target_url}")
    else:
        try:
            rule = RoutingRule.objects.select_related("environment__vendor").get(
                wa_id=wa_id, environment__vendor__code=vendor_code
            )
            target_url = rule.environment.target_url
            env_code = rule.environment.code
            env_name = rule.environment.name
            secure_vars = rule.environment.vendor.secure_variables
            
            logger.info(f"✅ Found specific routing rule for {vendor_code} {env_name}({env_code}):{wa_id} to {target_url}")
        except RoutingRule.DoesNotExist:
            try:
                default_env = Environment.objects.select_related("vendor").get(
                    vendor__code=vendor_code, is_default=True
                )
                target_url = default_env.target_url
                env_code = default_env.vendor.code
                env_name = default_env.vendor.name
                secure_vars = default_env.vendor.secure_variables
                logger.info(f"🎯 Using default environment for {vendor_code} {env_name}({env_code}):{wa_id} to {target_url}")
            except Environment.DoesNotExist:
                logger.error(
                    f"💥 ROUTING FAILED - No rule or default environment found for "
                    f"vendor '{vendor_code}' and wa_id '{wa_id}'"
                )
                return None

        cache.set(
            cache_key, {"target_url": target_url, "secure_variables": secure_vars, "env_name": env_name, "env_code": env_code}
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
        logger.info(f"🎉 Request successfully forwarded wa_id {wa_id} to {target_url}")
        return response
    except requests.exceptions.RequestException as e:
        logger.error(
            f"Failed to forward request for vendor '{vendor_code}' to {target_url}. Error: {e}"
        )
        return None
