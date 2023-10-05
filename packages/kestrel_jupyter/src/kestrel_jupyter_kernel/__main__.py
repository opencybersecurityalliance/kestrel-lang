from ipykernel.kernelapp import IPKernelApp
from kestrel_jupyter_kernel import KestrelKernel

if __name__ == "__main__":
    IPKernelApp.launch_instance(kernel_class=KestrelKernel)
