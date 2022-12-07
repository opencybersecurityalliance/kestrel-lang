from os.path import exists

from kestrel_jupyter_kernel.codemirror.setup import (
    update_codemirror_mode,
    _get_codemirror_file_paths,
)


def test_notebook_syntax_gen():
    js_paths = _get_codemirror_file_paths()
    update_codemirror_mode()
    for js_path in js_paths:
        assert exists(js_path)
