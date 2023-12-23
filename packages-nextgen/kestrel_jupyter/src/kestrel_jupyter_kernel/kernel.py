from ipykernel.kernelbase import Kernel
import logging

from kestrel.session import Session


_logger = logging.getLogger(__name__)


class KestrelKernel(Kernel):
    implementation = "kestrel"
    implementation_version = "2.0"
    language = "kestrel"
    language_version = "2.0"
    # https://jupyter-client.readthedocs.io/en/stable/messaging.html#msging-kernel-info
    language_info = {"name": "kestrel", "file_extension": ".hf"}
    banner = "Kestrel"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.kestrel_session = Session()

    def do_complete(self, code, cursor_pos):
        return {
            "matches": self.kestrel_session.do_complete(code, cursor_pos),
            "cursor_end": cursor_pos,
            "cursor_start": cursor_pos,
            "metadata": {},
            "status": "ok",
        }

    def do_execute(
        self, code, silent, store_history=True, user_expressions=None, allow_stdin=False
    ):
        if not silent:
            try:
                for result in self.kestrel_session.execute(code):
                    self.send_response(
                        self.iopub_socket,
                        "display_data",
                        {"data": {"text/html": result.to_html()}, "metadata": {}},
                    )

            except Exception as e:
                _logger.error("Exception occurred", exc_info=True)
                self.send_response(
                    self.iopub_socket, "stream", {"name": "stderr", "text": str(e)}
                )

        return {
            "status": "ok",
            "execution_count": self.execution_count,
            "payload": [],
            "user_expressions": {},
        }
