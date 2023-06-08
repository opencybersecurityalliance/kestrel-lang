################################################################
#             Batch Execution of Kestrel Huntflow
#
# Usage: `python3 -m kestrel [-v] [--debug] hunting.hf`
################################################################

import argparse
import logging

from kestrel.session import Session
from kestrel.utils import add_logging_handler, clear_logging_handlers


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

    clear_logging_handlers()
    if args.verbose:
        add_logging_handler(logging.StreamHandler(), args.debug)

    with Session(debug_mode=args.debug) as session:
        with open(args.huntflow, "r") as fp:
            huntflow = fp.read()
        outputs = session.execute(huntflow)
        results = "\n\n".join([o.to_string() for o in outputs])
        print(results)
