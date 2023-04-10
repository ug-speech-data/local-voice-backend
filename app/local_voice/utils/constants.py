from enum import Enum


class TransactionStatusMessages(Enum):
    PENDING = 'Transaction is pending'
    SUCCESS = 'Transaction successful'
    FAILED = 'Transaction failed'


class NetworkCodes(Enum):
    MTN = 'MTN'
    AIRTEL = 'AIRTEL'
    VODAFONE = 'VODAFONE'
    TIGO = 'TIGO'


class TransactionDirection(Enum):
    IN = 'IN'
    OUT = 'OUT'


class TransactionStatus(Enum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"


class ParticipantType(Enum):
    ASSISTED = "ASSISTED"
    INDEPENDENT = "INDEPENDENT"


class ValidationStatus(Enum):
    IN_REVIEW = "in_review"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    PENDING = "pending"


class TranscriptionStatus(Enum):
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    PENDING = "pending"
    CONFLICT = "conflict"
    IN_REVIEW = "in_review"
