from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from sqlalchemy import String, Integer, Numeric, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Request(Base):
    """
    Representa una solicitud de ampliación de carga enviada por un usuario Opersac.

    El flujo estándar comienza cuando un Opersac detecta que una carga nueva
    o ampliada supera la capacidad disponible y envía una solicitud formal al
    administrador. El administrador puede aprobarla o rechazarla.

    Lógica de creación según `circuit_id`:
        - Si `circuit_id` es None: se solicita la creación de un circuito nuevo
          en la barra indicada por `bar_type`.
        - Si `circuit_id` tiene valor: se solicita la creación de un sub-circuito
          dentro del circuito existente; los campos `sub_circuit_*` proveen los
          datos del nuevo sub-circuito.

    Estados posibles (campo `status`):
        - 'pending': en espera de revisión por el administrador.
        - 'approved': aprobada; se creó el circuito o sub-circuito correspondiente.
        - 'rejected': rechazada; el motivo se registra en `rejection_reason`.
    """

    __tablename__ = "requests"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    # Usuario Opersac que originó la solicitud
    opersac_user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False
    )
    station_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("stations.id"), nullable=False
    )
    # Tipo de barra sobre la que se solicita la ampliación: 'normal', 'emergencia' o 'continuidad'
    bar_type: Mapped[str] = mapped_column(String(20), nullable=False)
    # Circuito destino; si es None, se crea un circuito nuevo en lugar de un sub-circuito
    circuit_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("circuits.id"), nullable=True
    )
    local_item: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    # Carga adicional solicitada en kilovatios
    requested_load_kw: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False
    )
    # Factor de demanda propuesto para el nuevo circuito o sub-circuito
    fd: Mapped[Decimal] = mapped_column(
        Numeric(5, 4), nullable=False, default=1.0
    )
    # Campos del sub-circuito a crear (solo se usan cuando circuit_id tiene valor)
    sub_circuit_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    sub_circuit_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # Especificación del interruptor termomagnético del sub-circuito solicitado
    sub_circuit_itm: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    # Sección del cable del sub-circuito solicitado en mm²
    sub_circuit_mm2: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    justification: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # Estado de la solicitud: 'pending', 'approved' o 'rejected'
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending", index=True
    )
    # Motivo del rechazo; se rellena solo cuando status = 'rejected'
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # Administrador que revisó la solicitud
    reviewed_by: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True
    )
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    opersac_user = relationship("User", foreign_keys=[opersac_user_id])
    reviewer = relationship("User", foreign_keys=[reviewed_by])
    station = relationship("Station", back_populates="requests")
    circuit = relationship("Circuit", foreign_keys=[circuit_id])
