import time
import logging
from flask import request


logger = logging.getLogger("chatbot")


def init_logging(app):
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    @app.before_request
    def _start_timer():
        request._start_time = time.time()

    @app.after_request
    def _log_response(response):
        try:
            duration_ms = int((time.time() - getattr(request, "_start_time", time.time())) * 1000)
            logger.info(
                "%s %s %s %d %dms",
                request.remote_addr,
                request.method,
                request.path,
                response.status_code,
                duration_ms,
            )
        except Exception:
            pass
        return response

