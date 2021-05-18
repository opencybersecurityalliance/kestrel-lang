import os
import json
import notebook
import pkgutil
import kestrel


def update_codemirror_mode():
    codemirror_file_path = _get_codemirror_file_path()

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


def _get_codemirror_file_path():
    notebook_pkg_path = notebook.__path__[0]
    codemirror_dir_path = os.path.join(
        notebook_pkg_path, "static/components/codemirror/mode/kestrel"
    )
    if not os.path.isdir(codemirror_dir_path):
        try:
            os.mkdir(codemirror_dir_path)
        except PermissionError:
            pass
    return os.path.join(codemirror_dir_path, "kestrel.js")


def _instantiate_codemirror_mode_src():
    keywords = json.dumps(kestrel.get_keywords())
    codemirror_src = pkgutil.get_data(__name__, "kestrel_template.js").decode("utf-8")
    codemirror_src = codemirror_src.replace("<<<KEYWORDS>>>", keywords)
    return codemirror_src
