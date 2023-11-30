import pytest
from pandas import DataFrame
from uuid import uuid4

from kestrel.cache.inmemory import InMemoryCache


def test_inmemory_cache_set_get_del():
    c = InMemoryCache()
    idx = uuid4()
    df = DataFrame([1, 2, 3])
    c.store(idx, df)
    assert df.equals(c[idx])
    del c[idx]
    assert idx not in c


def test_inmemory_cache_constructor():
    ids = [uuid4() for i in range(5)]
    df = DataFrame([1, 2, 3])
    c = InMemoryCache({x:df for x in ids})
    for u in ids:
        assert df.equals(c[u])
    for u in ids:
        del c[u]
        assert u not in c
