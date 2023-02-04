import logging
from typeguard import typechecked
from firepit.sqlstorage import SqlStorage
from firepit.timestamp import to_datetime
from kestrel.symboltable.symtable import SymbolTable
from kestrel.syntax.reference import Reference
from kestrel.exceptions import (
    InvalidAttribute,
    KestrelInternalError,
)

_logger = logging.getLogger(__name__)


@typechecked
def make_deref_func(store: SqlStorage, symtable: SymbolTable):
    def deref(reference: Reference):
        _logger.debug(f"deref {reference}")
        entity_table = symtable[reference.variable].entity_table

        try:
            store_return = store.lookup(entity_table, reference.attribute)
        except InvalidAttr as e:
            _logger.warning(f"cannot deref {reference}. Invalid attribute in firepit.")
            raise InvalidAttribute(e.message)

        if reference.attribute not in store_return[0]:
            _logger.warning(f"firepit does not return the correct column.")
            raise KestrelInternalError(
                f"firepit does not return {reference} correctly."
            )

        values = [row[reference.attribute] for row in store_return]

        # filter out None
        values = [v for v in values if v]

        # dedup
        values = tuple(set(values))

        _logger.debug(f"deref results: {str(values)}")

        return values

    return deref


@typechecked
def make_var_timerange_func(store: SqlStorage, symtable: SymbolTable):
    def get_timerange(reference: Reference):
        entity_table = symtable[reference.variable].entity_table

        summary = store.summary(entity_table)
        if summary["first_observed"] is None:
            start = None
        else:
            start = to_datetime(summary["first_observed"])
        if summary["last_observed"] is None:
            end = None
        else:
            end = to_datetime(summary["last_observed"])
        if start is None and end is None:
            tr = None
        else:
            tr = (start, end)

        return tr

    return get_timerange
