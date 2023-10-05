import os
import json
import nbclassic
import notebook
import pkgutil
import kestrel


def update_codemirror_mode():
    for codemirror_file_path in _get_codemirror_file_paths():
        src_current = ""
        if os.path.isfile(codemirror_file_path):
            try:
                with open(codemirror_file_path) as fp:
                    src_current = fp.read()
            except PermissionError:
                pass

        src_latest = _instantiate_codemirror_mode_src()

        if src_latest != src_current:
            try:
                with open(codemirror_file_path, "w") as fp:
                    fp.write(src_latest)
            except PermissionError:
                pass


################################################################
#                       Private Functions
################################################################


def _get_codemirror_file_paths():
    paths = []
    for pkg_path in (notebook.__path__[0], nbclassic.__path__[0]):
        codemirror_dir = os.path.join(pkg_path, "static/components/codemirror/mode")
        if os.path.isdir(codemirror_dir):
            kestrel_dir = os.path.join(codemirror_dir, "kestrel")
            if not os.path.isdir(kestrel_dir):
                try:
                    os.mkdir(kestrel_dir)
                except PermissionError:
                    pass
            paths.append(os.path.join(kestrel_dir, "kestrel.js"))
    return paths


def _instantiate_codemirror_mode_src():
    keywords = json.dumps(kestrel.get_keywords())
    codemirror_src = pkgutil.get_data(__name__, "kestrel_template.js").decode("utf-8")
    codemirror_src = codemirror_src.replace("<<<KEYWORDS>>>", keywords)
    return codemirror_src
