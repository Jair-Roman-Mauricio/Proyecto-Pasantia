from decimal import Decimal
from sqlalchemy.orm import Session
from app.models.station import Station
from app.models.bar import Bar
from app.models.circuit import Circuit
from app.models.sub_circuit import SubCircuit


class EnergyCalculator:
    def __init__(self, db: Session):
        self.db = db

    def recalculate_station(self, station_id: int) -> Station:
        station = self.db.query(Station).filter(Station.id == station_id).first()
        if not station:
            return None

        bars = self.db.query(Bar).filter(Bar.station_id == station_id).all()
        bar_ids = [b.id for b in bars]

        total_md = Decimal("0")
        if bar_ids:
            circuits = (
                self.db.query(Circuit)
                .filter(Circuit.bar_id.in_(bar_ids))
                .filter(Circuit.status != "inactive")
                .all()
            )
            total_md = sum((c.md_kw for c in circuits), Decimal("0"))

            # Also sum sub-circuits
            circuit_ids = [c.id for c in circuits]
            if circuit_ids:
                sub_circuits = (
                    self.db.query(SubCircuit)
                    .filter(SubCircuit.circuit_id.in_(circuit_ids))
                    .filter(SubCircuit.status == "operative_normal")
                    .all()
                )
                total_md += sum((s.md_kw for s in sub_circuits), Decimal("0"))

        station.max_demand_kw = total_md
        station.available_power_kw = station.transformer_capacity_kw - total_md

        # Determine status color
        if station.available_power_kw < 0:
            station.status = "red"
        elif station.transformer_capacity_kw > 0:
            ratio = station.available_power_kw / station.transformer_capacity_kw
            if ratio < Decimal("0.2"):
                station.status = "yellow"
            else:
                station.status = "green"
        else:
            station.status = "green"

        self.db.commit()
        self.db.refresh(station)
        return station

    def check_capacity(self, bar_id: int, new_md_kw: Decimal) -> dict:
        """Check if adding new_md_kw to a bar's station would exceed capacity."""
        bar = self.db.query(Bar).filter(Bar.id == bar_id).first()
        if not bar:
            return {"can_add": False, "message": "Barra no encontrada"}

        station = self.db.query(Station).filter(Station.id == bar.station_id).first()
        remaining = station.available_power_kw - new_md_kw

        return {
            "can_add": remaining >= 0,
            "available_before": float(station.available_power_kw),
            "available_after": float(remaining),
            "station_name": station.name,
            "message": (
                "Capacidad suficiente"
                if remaining >= 0
                else f"Excede la capacidad disponible por {abs(float(remaining))} kW"
            ),
        }

    def get_bar_power_summary(self, bar_id: int) -> dict:
        """Get power summary for a specific bar."""
        bar = self.db.query(Bar).filter(Bar.id == bar_id).first()
        if not bar:
            return None

        circuits = (
            self.db.query(Circuit)
            .filter(Circuit.bar_id == bar_id, Circuit.status != "inactive")
            .all()
        )

        total_pi = sum((c.pi_kw for c in circuits), Decimal("0"))
        total_md = sum((c.md_kw for c in circuits), Decimal("0"))

        # Also sum sub-circuits
        circuit_ids = [c.id for c in circuits]
        if circuit_ids:
            sub_circuits = (
                self.db.query(SubCircuit)
                .filter(SubCircuit.circuit_id.in_(circuit_ids))
                .filter(SubCircuit.status == "operative_normal")
                .all()
            )
            total_pi += sum((s.pi_kw for s in sub_circuits), Decimal("0"))
            total_md += sum((s.md_kw for s in sub_circuits), Decimal("0"))

        return {
            "total_installed_power_kw": float(total_pi),
            "total_max_demand_kw": float(total_md),
            "max_board_capacity_kw": float(bar.capacity_kw),
            "max_board_capacity_a": float(bar.capacity_a),
            "available_power_kw": float(bar.capacity_kw - total_md),
        }
