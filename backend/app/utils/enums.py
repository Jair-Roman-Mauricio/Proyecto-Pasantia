import enum


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    OPERSAC = "opersac"


class UserStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    REPORTED = "reported"


class StationStatus(str, enum.Enum):
    RED = "red"
    YELLOW = "yellow"
    GREEN = "green"


class BarType(str, enum.Enum):
    NORMAL = "normal"
    EMERGENCY = "emergency"
    CONTINUITY = "continuity"


class BarStatus(str, enum.Enum):
    OPERATIVE = "operative"
    INACTIVE = "inactive"


class CircuitStatus(str, enum.Enum):
    OPERATIVE_NORMAL = "operative_normal"
    RESERVE_R = "reserve_r"
    RESERVE_EQUIPPED_RE = "reserve_equipped_re"
    INACTIVE = "inactive"


class RequestStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class NotificationType(str, enum.Enum):
    RESERVE_NO_CONTACT = "reserve_no_contact"
    NEGATIVE_ENERGY = "negative_energy"
    REQUEST_PENDING = "request_pending"
    SYSTEM = "system"


class ObservationSeverity(str, enum.Enum):
    URGENT = "urgent"
    WARNING = "warning"
    RECOMMENDATION = "recommendation"
