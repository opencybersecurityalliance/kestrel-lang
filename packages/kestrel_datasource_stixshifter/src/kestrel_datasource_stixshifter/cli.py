import argparse
import datetime
import logging
import sys
from kestrel_datasource_stixshifter.diagnosis import Diagnosis
from kestrel_datasource_stixshifter.connector import setup_connector_module
from firepit.timestamp import timefmt


def default_patterns(start=None, stop=None, last_minutes=0):
    if start:
        start_time = f"START t'{start}'"
        stop_time = f"STOP t'{stop}'"
    else:
        to_time = datetime.datetime.utcnow()
        from_time = timefmt(to_time - datetime.timedelta(minutes=last_minutes))
        to_time = timefmt(to_time)
        start_time = f"START t'{from_time}'"
        stop_time = f"STOP t'{to_time}'"
    patterns = [
        "[ipv4-addr:value != '255.255.255.255']",
        "[process:pid > 0]",
        "[email-addr:value != 'null@xyz.com']",
    ]
    return [" ".join([p, start_time, stop_time]) for p in patterns]


def stix_shifter_diag():
    parser = argparse.ArgumentParser(
        description="Kestrel stix-shifter data source interface diagnosis"
    )
    parser.add_argument(
        "datasource", help="data source name specified in stixshifter.yaml"
    )
    parser.add_argument(
        "--ignore-cert",
        help="ignore certificate (PKI) verification in connector verification",
        action="store_false",
    )
    parser.add_argument(
        "-p",
        "--stix-pattern",
        help="STIX pattern in double quotes",
    )
    parser.add_argument(
        "-f",
        "--pattern-file",
        help="write your STIX pattern in a file and put the file path here to use for diagnosis",
    )
    parser.add_argument(
        "--stop-at-now",
        help="ignored (retained for backwards compatibility)",
        action="store_true",
    )
    parser.add_argument(
        "--start",
        help="start time for default pattern search (%Y-%m-%dT%H:%M:%S.%fZ)",
    )
    parser.add_argument(
        "--stop",
        help="stop time for default pattern search (%Y-%m-%dT%H:%M:%S.%fZ)",
    )
    parser.add_argument(
        "--last-minutes",
        help="relative timespan for default pattern searches in minutes",
        default=5,
        type=int,
    )
    parser.add_argument(
        "-t",
        "--translate-only",
        help="Only translate pattern; don't transmit",
        action="store_true",
    )
    parser.add_argument(
        "-d", "--debug", help="Enable DEBUG logging", action="store_true"
    )
    args = parser.parse_args()

    if args.debug:
        logger = logging.getLogger()
        logger.setLevel(logging.DEBUG)
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)
        formatter = logging.Formatter("%(levelname)s: %(message)s")
        ch.setFormatter(formatter)
        logger.addHandler(ch)

    if (args.start and not args.stop) or (args.stop and not args.start):
        print(
            "Must specify both --start and --stop for absolute time range; else use --last-minutes",
            file=sys.stderr,
        )
        parser.print_usage(sys.stderr)
        sys.exit(1)

    if args.stix_pattern:
        patterns = [args.stix_pattern]
    elif args.pattern_file:
        with open(args.pattern_file) as pf:
            patterns = [pf.read()]
    else:
        patterns = default_patterns(args.start, args.stop, args.last_minutes)

    diag = Diagnosis(args.datasource)

    # 1. check config manually
    diag.diagnose_config()

    # 2. setup connector and ping
    setup_connector_module(
        diag.connector_name, diag.allow_dev_connector, args.ignore_cert
    )

    # 3. query translation test
    diag.diagnose_translate_query(patterns[0])

    if not args.translate_only:
        # 4. transmit ping test
        diag.diagnose_ping()

        # 5. single-batch query execution test
        diag.diagnose_run_query_and_retrieval_result(patterns, 1)

        # 6. multi-batch query execution test
        diag.diagnose_run_query_and_retrieval_result(patterns, 5)
