#!/usr/bin/env python3

################################################################
#                   Setup Kestrel Jupyter Kernel
#
# This module setups the Kestrel Jupyter kernel:
#   1. install the kernel to Jupyter environment (local env)
#   2. generate codemirror mode for Kestrel based on the
#      installed kestrel Python package for syntax highlighting
#   3. install the codemirror mode into Jupyter
#
# Usage: `python3 -m kestrel_jupyter_kernel.setup`
#
################################################################

import os
import tempfile
import json
from jupyter_client.kernelspec import KernelSpecManager
from kestrel_jupyter_kernel.codemirror.setup import update_codemirror_mode

_KERNEL_SPEC = {
    "argv": ["python3", "-m", "kestrel_jupyter_kernel", "-f", "{connection_file}"],
    "display_name": "Kestrel",
    "language": "kestrel",
}


def install_kernelspec():
    with tempfile.TemporaryDirectory() as tmp_dirname:
        kernel_dirname = os.path.join(tmp_dirname, "kestrel_kernel")
        os.mkdir(kernel_dirname)
        kernel_filename = os.path.join(kernel_dirname, "kernel.json")
        with open(kernel_filename, "w") as kf:
            json.dump(_KERNEL_SPEC, kf)

        m = KernelSpecManager()
        m.install_kernel_spec(kernel_dirname, "kestrel", user=True)


if __name__ == "__main__":

    print("Setup Kestrel Jupyter Kernel")
    print("  Install new Jupyter kernel ...", end=" ")
    install_kernelspec()
    print("done")

    # generate and install kestrel codemirrmor mode
    print("  Compute and install syntax highlighting ...", end=" ")
    update_codemirror_mode()
    print("done")
