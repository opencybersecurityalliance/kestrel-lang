from abc import ABC, abstractmethod


class AbstractReturnStruct(ABC):
    """The abstract class for creating return objects.

    1. it should have a constructor for the interface to create it. The
       interface should specify the ``query_id`` in the constructor.

    2. it should have a :attr:`load_to_store` method for Kestrel runtime to load data from it.

    """

    @abstractmethod
    def load_to_store(self, store):
        """Load the data (from data source) to store.

        Returns:
            str: the ``query_id``, which is a identifier in the store
            associated with the loaded data entries.

        """
        return ""


class ReturnFromFile(AbstractReturnStruct):
    """The return structure when the data source interface uses files as intermediate storage before loading to store.

    Args:
        query_id (str): typically just a UUID.
        file_paths ([str]): the list of stix bundle file paths.

    """

    def __init__(self, query_id, file_paths):
        self.query_id = query_id
        self.file_paths = file_paths

    def load_to_store(self, store):
        store.cache(self.query_id, self.file_paths)
        return self.query_id


class ReturnFromStore(AbstractReturnStruct):
    """The return structure when the data source interface directly operates on the store.

    Args:
        query_id (str): typically just a UUID.

    """

    def __init__(self, query_id):
        self.query_id = query_id

    def load_to_store(self, store):
        return self.query_id
