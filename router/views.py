import json
import logging
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt

from wa_router.utils.logging_utils import log_object
from . import services
from django.conf import settings

logger = logging.getLogger("router")


@csrf_exempt
def meta_webhook_receiver(request: HttpRequest, vendor_code: str) -> HttpResponse:
    if request.method == "GET":
        challenge = request.GET.get("hub.challenge")
        verify_token = request.GET.get("hub.verify_token")
        mode = request.GET.get("hub.mode")
        if mode == 'subscribe' and verify_token == settings.WHATSAPP_VERIFY_TOKEN:
            return HttpResponse(challenge, status=200)
        return HttpResponse("Invalid verification request", status=400)

    elif request.method == "POST":
        try:
            request_body = json.loads(request.body)
        except json.JSONDecodeError:
            return HttpResponse("Invalid JSON", status=400)

        response = services.process_and_forward_request(
            vendor_code, request_body, request.headers
        )

        if response:
            return HttpResponse(
                content=response.content,
                status=200,
                content_type=response.headers.get("Content-Type"),
            )

        return HttpResponse("Could not process request.", status=200)

    return HttpResponse("Method not allowed", status=405)
