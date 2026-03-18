"""
Enumeraciones del dominio para la aplicación Línea 1 Metro.

Centraliza todos los valores válidos de campos de estado, tipo y severidad
usados en modelos, schemas y lógica de negocio del backend.
"""

import enum


class UserRole(str, enum.Enum):
    """Roles disponibles para los usuarios del sistema."""

    ADMIN = "admin"       # Acceso total: gestión, auditoría, backups y aprobación de solicitudes
    OPERSAC = "opersac"   # Acceso limitado por permisos asignados individualmente


class UserStatus(str, enum.Enum):
    """Estado de la cuenta de un usuario."""

    ACTIVE = "active"       # Usuario habilitado, puede autenticarse
    INACTIVE = "inactive"   # Usuario deshabilitado manualmente por un admin
    REPORTED = "reported"   # Usuario marcado por incidencia; bloqueado hasta revisión


class StationStatus(str, enum.Enum):
    """Estado de capacidad de una estación eléctrica (calculado automáticamente)."""

    RED = "red"        # Capacidad disponible crítica (≤ 10 % del transformador)
    YELLOW = "yellow"  # Capacidad disponible en nivel de advertencia (10–25 %)
    GREEN = "green"    # Capacidad disponible normal (> 25 %)


class BarType(str, enum.Enum):
    """Tipo de barra eléctrica dentro de una estación."""

    NORMAL = "normal"           # Barra de suministro normal (operación estándar)
    EMERGENCY = "emergency"     # Barra de emergencia (alimentada por grupo electrógeno)
    CONTINUITY = "continuity"   # Barra de continuidad (UPS / suministro ininterrumpido)


class BarStatus(str, enum.Enum):
    """Estado operativo de una barra eléctrica."""

    OPERATIVE = "operative"  # Barra en servicio
    INACTIVE = "inactive"    # Barra fuera de servicio


class CircuitStatus(str, enum.Enum):
    """Estado operativo de un circuito eléctrico."""

    OPERATIVE_NORMAL = "operative_normal"         # Circuito en operación normal
    RESERVE_R = "reserve_r"                       # Reserva simple (sin equipar)
    RESERVE_EQUIPPED_RE = "reserve_equipped_re"   # Reserva equipada (instalada, sin carga activa)
    INACTIVE = "inactive"                         # Circuito fuera de servicio


class RequestStatus(str, enum.Enum):
    """Estado de una solicitud de ampliación de carga."""

    PENDING = "pending"    # Solicitud enviada, pendiente de revisión por el admin
    APPROVED = "approved"  # Solicitud aprobada; circuito o sub-circuito ya creado
    REJECTED = "rejected"  # Solicitud rechazada con motivo indicado por el admin


class NotificationType(str, enum.Enum):
    """Tipo de notificación automática generada por el sistema."""

    RESERVE_NO_CONTACT = "reserve_no_contact"  # Reserva próxima a vencer sin contacto registrado
    NEGATIVE_ENERGY = "negative_energy"        # Estación con energía disponible negativa (sobrecarga)
    REQUEST_PENDING = "request_pending"        # Nueva solicitud de ampliación pendiente de revisión
    SYSTEM = "system"                          # Notificación genérica del sistema


class ObservationSeverity(str, enum.Enum):
    """Nivel de severidad de una observación técnica."""

    URGENT = "urgent"                  # Requiere atención inmediata
    WARNING = "warning"                # Situación a monitorear
    RECOMMENDATION = "recommendation"  # Sugerencia de mejora sin urgencia
