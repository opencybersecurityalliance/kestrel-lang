from jupyter_client.kernelspec import KernelSpecManager

from kestrel_jupyter_kernel.setup import install_kernelspec


def test_kernel_install():
    m = KernelSpecManager()
    ks = m.get_all_specs()
    if "kestrel" in ks:
        m.remove_kernel_spec("kestrel")

    install_kernelspec()
    assert "kestrel" in m.get_all_specs()
