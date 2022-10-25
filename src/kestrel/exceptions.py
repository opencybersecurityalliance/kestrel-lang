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
        self.error = error[:-1] if error[-1] == "\n" else error

        self.suggestion = (
            suggestion
            if (not suggestion or suggestion[-1] == ".")
            else suggestion + "."
        )

    def __str__(self):
        return f"[ERROR] {self.__class__.__name__}: {self.error}\n{self.suggestion}"


class KestrelInternalError(KestrelException):
    def __init__(self, error):
        super().__init__(error, "please open a github issue to report")


class KestrelNotImplemented(KestrelException):
    def __init__(self, error):
        super().__init__(
            "Functionality not implemented: " + error,
            "please search for the github issue to add comment",
        )


################################################################
#                     Kestrel Session Errors
################################################################


class InvalidConfiguration(KestrelException):
    def __init__(self, error, suggestion):
        super().__init__(error, suggestion)


class DebugCacheLinkOccupied(KestrelException):
    def __init__(self, link):
        super().__init__(
            f"the path '{link}' is used by other users and cannot be removed (permission error).",
            "Try manually remove the file/link or set 'debug.cache_directory_prefix' in the Kestrel config file to other values",
        )


################################################################
#                       Kestrel Syntax Errors
################################################################


class KestrelSyntaxError(KestrelException):
    def __init__(self, line, column, invalid_term_type, invalid_term_value, expected):
        self.line = line
        self.column = column
        self.invalid_term_type = invalid_term_type
        self.invalid_term_value = invalid_term_value
        self.expected = list(expected)
        self._expects_str = (
            f'expects "{self.expected[0]}"'
            if len(self.expected) == 1
            else f"expects one of {self.expected}"
        )
        super().__init__(
            f'invalid {self.invalid_term_type} "{self.invalid_term_value}" at line {self.line} column {self.column}, {self._expects_str}',
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


class InvalidECGPattern(KestrelException):
    pass


class MissingDataSource(KestrelException):
    def __init__(self, stmt):
        super().__init__(f"missing datasource in statement: {str(stmt)}")


class VariableNotExist(KestrelException):
    def __init__(self, var_name):
        self.var_name = var_name
        super().__init__(
            f'variable "{var_name}" does not exist', "check the variable used"
        )


class UnsupportedRelation(KestrelException):
    def __init__(self, entity_x, relation, entity_y):
        super().__init__(
            f'unsupported relation "{entity_x}--{relation}--{entity_y}"',
            "check for supported relations and entity types in the documentation",
        )


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


class MissingEntityAttribute(KestrelException):
    def __init__(self, var_name, attribute):
        super().__init__(
            f'variable "{var_name}" does not have required attribute "{attribute}"',
            "remove transform or specify different variable in the Kestrel command",
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
    def __init__(self, error, suggestion=""):
        if not suggestion:
            suggestion = "please check data source config or test the query manually"
        super().__init__(
            error,
            suggestion,
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
    def __init__(self, error, suggestion=""):
        suggestion = "report to analytics developer" if not suggestion else suggestion
        super().__init__(error, suggestion)


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


class InvalidAnalyticsArgumentCount(KestrelException):
    def __init__(self, analytics_name, num_received, num_expected):
        super().__init__(
            f'the analytics "{analytics_name}" takes {num_expected} Kestrel variables, not {num_received} as given in APPLY.'
        )


class InvalidAnalyticsInput(KestrelException):
    def __init__(self, type_received, types_expected):
        typelist = ", ".join([f'"{t}"' for t in types_expected])
        super().__init__(
            f'received unsupported type "{type_received}"; expected one of {typelist}'
        )


class InvalidAnalyticsOutput(KestrelException):
    def __init__(self, analytics_name, return_type):
        super().__init__(
            f"unsupported return type {return_type} from analytics: {analytics_name}"
        )
