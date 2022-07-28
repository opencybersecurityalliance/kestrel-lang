import pytest

from kestrel.session import Session
from kestrel.codegen import commands


def test_prefetch_config():
    with Session() as s:
        # by default, no excluded entity type in config
        assert commands._is_prefetch_allowed_in_config(s.config["prefetch"], "get", "process") == True
        # by default, no excluded entity type in config
        assert commands._is_prefetch_allowed_in_config(s.config["prefetch"], "find", "file") == True
