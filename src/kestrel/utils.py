import pathlib
import os
import uuid
import collections.abc
import logging


def unescape_quoted_string(s):
    if s.startswith("r"):
        return s[2:-1]
    else:
        return s[1:-1].encode("utf-8").decode("unicode_escape")


def lowered_str_list(xs):
    return [x.lower() for x in xs if isinstance(x, str)]


def update_nested_dict(dict_old, dict_new):
    if dict_new:
        for k, v in dict_new.items():
            if isinstance(v, collections.abc.Mapping) and k in dict_old:
                dict_old[k] = update_nested_dict(dict_old[k], v)
            else:
                dict_old[k] = v
    return dict_old


def remove_empty_dicts(ds):
    # remove dict with all values as None in list({string:string})
    # this is the results from SQL query
    return [d for d in ds if set(d.values()) != {None}]


def dedup_dicts(ds):
    # deduplicate list({string:string})
    # this is the results from SQL query
    return [dict(s) for s in set(frozenset(d.items()) for d in ds)]


def dedup_ordered_dicts(ds):
    # deduplicate list({string:string})
    # maintain the order if seen
    res = []
    seen = set()
    for d in ds:
        s = str(d)
        if s not in seen:
            res.append(d)
        seen.add(s)
    return res


def subgroup_list(xs, gsize):
    return [xs[i : i + gsize] for i in range(0, len(xs), gsize)]


def mkdtemp():
    # create a temporary directory and return it (named after a random uuid)
    ps = None
    while not ps or pathlib.Path(ps).exists():
        ps = str(uuid.uuid4())
    p = pathlib.Path(ps)
    p.mkdir(parents=True, exist_ok=True)
    return p


def add_logging_handler(handler, if_debug):
    fmt = "%(asctime)s %(levelname)s %(name)s %(message)s"
    datefmt = "%H:%M:%S"
    formatter = logging.Formatter(fmt=fmt, datefmt=datefmt)

    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    current_logging_level = root_logger.getEffectiveLevel()
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.DEBUG if if_debug else logging.INFO)

    return handler, current_logging_level


def clear_logging_handlers():
    root_logger = logging.getLogger()
    for h in root_logger.handlers[:]:
        root_logger.removeHandler(h)
        h.close()


def resolve_path_in_kestrel_env_var():
    for key in os.environ:
        if key.startswith("KESTREL") or key.startswith("kestrel"):
            path = os.environ[key]
            if os.path.exists(path):
                os.environ[key] = resolve_path(path)


def resolve_path(path):
    return os.path.abspath(os.path.expanduser(os.path.expandvars(path)))


class set_current_working_directory:
    def __init__(self, new_cwd):
        self.tmp_cwd = new_cwd

    def __enter__(self):
        self.cwd = os.getcwd()
        os.chdir(self.tmp_cwd)

    def __exit__(self, exception_type, exception_value, traceback):
        os.chdir(self.cwd)
