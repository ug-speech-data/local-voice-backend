from enum import Enum


class PayHubStatusCodes(Enum):
    """
    PayHub Status Codes
    """
    FAILED = "107"
    PENDING = "004"
    SUCCESS = "000"
    DUPLICATE_TRANSACTION = "106"
