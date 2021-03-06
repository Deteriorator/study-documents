import os
import tempfile
import random
random.seed()

from nose.tools import *

from tinydb.storages import JSONStorage, MemoryStorage

path = None
element = {'none': [None, None], 'int': 42, 'float': 3.1415899999999999,
           'list': ['LITE', 'RES_ACID', 'SUS_DEXT'],
           'dict': {'hp': 13, 'sp': 5},
           'bool': [True, False, True, False]}


def setup():
    global path, element

    # Generate temp file
    tmp = tempfile.NamedTemporaryFile(delete=False)
    tmp.file.close()  # Close file handle
    path = tmp.name


def teardown():
    # Cleanup
    # Fix for pypy: Run garbace collection because otherwise pypy didn't
    # destroy the storage object and thus keeping open handles on the temp
    # directory.
    import gc
    gc.collect()

    os.unlink(path)


def test_json():
    # Write contents
    storage = JSONStorage(path)
    storage.write(element)

    # Verify contents
    assert_equal(element, storage.read())


def test_in_memory():
    # Write contents
    storage = MemoryStorage()
    storage.write(element)

    # Verify contents
    assert_equal(element, storage.read())
