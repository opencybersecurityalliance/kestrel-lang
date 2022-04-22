from os.path import exists

from kestrel_jupyter_kernel.codemirror.setup import (
    update_codemirror_mode,
    _get_codemirror_file_path,
)


def test_notebook_syntax_gen():
    js_path = _get_codemirror_file_path()
    update_codemirror_mode()
    assert exists(js_path)
