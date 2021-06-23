################################################################
#                     Generic Errors
################################################################


class KestrelException(Exception):
    """Generic Kestrel Exception

    Args:
        error (str): error message.
        suggestion (str): suggestion to fix the issue.
    """

    def __init__(self, error, suggestion=""):
        self.error = error if error[-1] == "." else error + "."
        self.suggestion = suggestion if suggestion[-1] == "." else suggestion + "."

    def __str__(self):
        return f"[ERROR] {self.__class__.__name__}: {self.error} {self.suggestion}"


class KestrelInternalError(KestrelException):
    def __init__(self, error):
        super().__init__(error, "please open a github issue to report")


################################################################
#                     Kestrel Session Errors
################################################################


class NoValidConfiguration(KestrelException):
    def __init__(self):
        super().__init__(
            "no valid configuration files found",
            'reinstall package with "pip install". report bug if not solved',
        )


################################################################
#                       Kestrel Syntax Errors
################################################################


class KestrelSyntaxError(KestrelException):
    def __init__(self, line, column, invalid_term_type, invalid_term_value):
        self.line = line
        self.column = column
        self.invalid_term_type = invalid_term_type
        self.invalid_term_value = invalid_term_value
        super().__init__(
            f'invalid {self.invalid_term_type} "{self.invalid_term_value}" at line {self.line} column {self.column}',
            "rewrite the failed statement",
        )


class InvalidStixPattern(KestrelException):
    def __init__(
        self,
        stix,
        line=None,
        column=None,
        invalid_term_type=None,
        invalid_term_value=None,
    ):
        self.stix = stix
        self.line = line
        self.column = column
        self.invalid_term_type = invalid_term_type
        self.invalid_term_value = invalid_term_value
        msg = f'invalid STIX pattern "{stix}"'
        if self.invalid_term_value:
            details = f': invalid {self.invalid_term_type} "{self.invalid_term_value}" at line {self.line} column {self.column}'
            msg = msg + details
        super().__init__(msg, "rewrite the STIX pattern")


class VariableNotExist(KestrelException):
    def __init__(self, var_name):
        super().__init__(
            f'variable "{var_name}" does not exist', "check the variable used"
        )


class UnsupportedRelation(KestrelException):
    def __init__(self, entity_x, relation, entity_y):
        super().__init__(
            f'unsupported relation "{entity_x}--{relation}--{entity_y}"',
            "check for supported relations and entity types in the documentation",
        )


class UnsupportedStixSyntax(KestrelException):
    def __init__(self, msg):
        super().__init__(msg, "rewrite the STIX pattern")


################################################################
#                 Kestrel Code Generation Errors
################################################################


class EmptyInputVariable(KestrelException):
    def __init__(self, var_name):
        super().__init__(
            f'empty input variable "{var_name}"',
            "rewrite the command to use a non-empty variable as input",
        )


class InvalidAttribute(KestrelException):
    def __init__(self, attribute):
        super().__init__(
            f'invalid attribute "{attribute}"',
            "rewrite the command with a valid attribute",
        )


class NonUniformEntityType(KestrelException):
    def __init__(self, etypes):
        super().__init__(
            f"there are more than one entity types in input data: {etypes}",
            "provide homogeneous entities to construct a Kestrel variable",
        )


class MissingEntityType(KestrelException):
    def __init__(self):
        super().__init__(
            'input data does not have "type" column',
            'add "type" column to data or specify entity type in the Kestrel command',
        )


################################################################
#                     Data Source Errors
################################################################


class DataSourceConnectionError(KestrelException):
    def __init__(self, uri):
        super().__init__(
            f"cannot establish connection to {uri}",
            "check URI for typos; please test network connection",
        )


class DataSourceManagerInternalError(KestrelInternalError):
    def __init__(self, error):
        super().__init__(error)


class InvalidDataSource(KestrelException):
    def __init__(self, uri, itf, msg=""):
        super().__init__(
            f'invalid data source "{uri}" at interface "{itf}". {msg}',
            "please check data source configuration",
        )


class DataSourceError(KestrelException):
    def __init__(self, error):
        super().__init__(
            f"data source internal error: {error}", "please test data source manually"
        )


class DataSourceInterfaceNotFound(KestrelException):
    def __init__(self, scheme):
        super().__init__(
            f'interface handling "{scheme}://" does not exist',
            "(re)install the missing/broken data source interface package",
        )


class InvalidDataSourceInterfaceImplementation(Exception):
    def __init__(self, error):
        super().__init__(error, "report to data source interface developer")


class ConflictingDataSourceInterfaceScheme(KestrelException):
    def __init__(self, itf_a, itf_b, scheme):
        super().__init__(
            f'conflicting data source interface scheme "{scheme}" between "{itf_a.__module__}" and "{itf_b.__module__}"',
            "uninstall one of the data source interfaces",
        )


################################################################
#                       Analytics Errors
################################################################


class AnalyticsManagerInternalError(KestrelInternalError):
    def __init__(self, error):
        super().__init__(error)


class InvalidAnalytics(KestrelException):
    def __init__(self, name, itf, msg=""):
        super().__init__(
            f'invalid analytics "{name}" at interface "{itf}". {msg}',
            "please check analytics availability",
        )


class AnalyticsError(KestrelException):
    def __init__(self, error):
        super().__init__(error, "report to analytics developer")


class AnalyticsInterfaceNotFound(KestrelException):
    def __init__(self, scheme):
        super().__init__(
            f'interface handling "{scheme}://" does not exist',
            "(re)install the missing/broken data source interface package",
        )


class InvalidAnalyticsInterfaceImplementation(Exception):
    def __init__(self, error):
        super().__init__(error, "report to analytics interface developer")


class ConflictingAnalyticsInterfaceScheme(KestrelException):
    def __init__(self, itf_a, itf_b, scheme):
        super().__init__(
            f'conflicting analytics interface scheme "{scheme}" between "{itf_a.__module__}" and "{itf_b.__module__}"',
            "uninstall one of the analytics interfaces",
        )
