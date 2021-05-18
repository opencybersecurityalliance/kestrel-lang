################################################################
#             Batch Execution of Kestrel Huntflow
#
# Usage: `python3 -m kestrel [-v] [--debug] hunting.hf`
################################################################

import argparse
import logging
import os

from kestrel.session import Session


def logging_setup(session, verbose_mode, debug_mode):
    # setup logging format, channel and granularity
    log_format = "%(asctime)s %(levelname)s %(name)s %(message)s"
    log_console = logging.StreamHandler()
    if session:
        log_file_path = os.path.join(session.runtime_directory, "session.log")
        log_file = logging.FileHandler(log_file_path)
        log_handlers = [log_console, log_file] if verbose_mode else [log_file]
    else:
        log_handlers = [log_console]
    logging.basicConfig(
        format=log_format,
        datefmt="%H:%M:%S",
        level=logging.DEBUG if debug_mode else logging.INFO,
        handlers=log_handlers,
    )


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Kestrel Interpreter")
    parser.add_argument("huntflow", help="huntflow in .hf file")
    parser.add_argument(
        "-v", "--verbose", help="print verbose log", action="store_true"
    )
    parser.add_argument(
        "--debug", help="debug level log (default is info level)", action="store_true"
    )
    args = parser.parse_args()

    logging_setup(None, args.verbose, args.debug)
    with Session(debug_mode=args.debug) as session:
        logging_setup(session, args.verbose, args.debug)
        with open(args.huntflow, "r") as fp:
            huntflow = fp.read()
        outputs = session.execute(huntflow)
        results = "\n\n".join([o.to_string() for o in outputs])
        print(results)
