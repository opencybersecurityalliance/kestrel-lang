from typing import Optional, Union, List
from dataclasses import dataclass
from pandas import DataFrame

STOP_SIGN = "STOP"


@dataclass
class WorkerLog:
    level: int
    log: str


# if success == True, data and offset is not None
# if success == False, log is not None
@dataclass
class TransmissionResult:
    worker: str
    success: bool
    data: Optional[List[dict]]
    offset: Optional[int]
    log: Optional[WorkerLog]


# if success == True, data is not None
# if success == False, log is not None
@dataclass
class TranslationResult:
    worker: str
    success: bool
    data: Union[None, dict, DataFrame]
    log: Optional[WorkerLog]
