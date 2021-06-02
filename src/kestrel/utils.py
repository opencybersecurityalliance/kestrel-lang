import pathlib
import os
import uuid


KESTREL_CONFIG = pathlib.Path("kestrel") / "kestrel.toml"


def config_paths():
    # latter ones will override former ones
    paths = [
        # pip install with root
        pathlib.Path("/") / KESTREL_CONFIG,
        # pip install in venv
        pathlib.Path(os.getenv("VIRTUAL_ENV", "")) / "etc" / KESTREL_CONFIG,
        # conda environment install
        pathlib.Path(os.getenv("CONDA_PREFIX", "")) / "etc" / KESTREL_CONFIG,
        # GitHub Action: Ubuntu environment
        pathlib.Path(os.getenv("pythonLocation", "")) / "etc" / KESTREL_CONFIG,
        # pip install --user
        pathlib.Path(os.getenv("HOME", "")) / ".local" / "etc" / KESTREL_CONFIG,
        # user-defined configuration
        pathlib.Path(os.getenv("HOME", "")) / ".config" / KESTREL_CONFIG,
    ]

    path_dedups = []
    for path in paths:
        if path not in path_dedups:
            path_dedups.append(path)

    return path_dedups


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


class set_current_working_directory:
    def __init__(self, new_cwd):
        self.tmp_cwd = new_cwd

    def __enter__(self):
        self.cwd = os.getcwd()
        os.chdir(self.tmp_cwd)

    def __exit__(self, exception_type, exception_value, traceback):
        os.chdir(self.cwd)
