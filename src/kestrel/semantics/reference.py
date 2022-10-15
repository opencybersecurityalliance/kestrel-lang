import logging

_logger = logging.getLogger(__name__)


def make_deref_func(store, symtable):
    def deref(reference):
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

        _logger.debug(f"deref results: {str(values)}")

        return values

    return deref
