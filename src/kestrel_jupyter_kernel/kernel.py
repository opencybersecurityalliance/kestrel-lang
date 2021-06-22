from ipykernel.kernelbase import Kernel
import pandas as pd
import os
import logging

from kestrel.session import Session
from kestrel_jupyter_kernel.config import LOG_FILE_NAME


class KestrelKernel(Kernel):
    implementation = "kestrel"
    implementation_version = "1.0"
    language = "kestrel"
    language_version = "1.0"
    language_info = {"name": "Kestrel", "codemirror_mode": "kestrel"}
    banner = "Kestrel"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.kestrel_session = Session()
        _set_logging(
            self.kestrel_session.debug_mode,
            os.path.join(self.kestrel_session.runtime_directory, LOG_FILE_NAME)
        )

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

        errmsg = None

        if not silent:
            try:
                outputs = self.kestrel_session.execute(code)
                output_html = "\n".join([x.to_html() for x in outputs])
                self.send_response(
                    self.iopub_socket,
                    "display_data",
                    {"data": {"text/html": output_html}},
                )

            except Exception as e:
                self.send_response(
                    self.iopub_socket, "stream", {"name": "stderr", "text": str(e)}
                )

        return {
            "status": "ok",
            "execution_count": self.execution_count,
            "payload": [],
            "user_expressions": {},
        }

    def _at_shutdown(self):
        self.kestrel_session.close()
        super()._at_shutdown()


def _set_logging(debug_flag, log_file_path):
    logging.basicConfig(
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        datefmt="%H:%M:%S",
        level=logging.DEBUG if debug_flag else logging.INFO,
        handlers=[logging.FileHandler(log_file_path)],
    )
