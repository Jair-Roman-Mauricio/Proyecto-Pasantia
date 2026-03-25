from decimal import Decimal
from app.subest_client import get_subest_client


class EnergyCalculator:
    def __init__(self):
        self.client = get_subest_client()

    def recalculate_station(self, station_id: int) -> dict | None:
        result = self.client.table("stations").select("*").eq("id", station_id).execute()
        if not result.data:
            return None
        station = result.data[0]

        bars = self.client.table("bars").select("*").eq("station_id", station_id).execute().data
        REDUCED = Decimal("0.75")
        total_md = Decimal("0")

        for bar in bars:
            circuits = self.client.table("circuits").select("id,md_kw").eq("bar_id", bar["id"]).neq("status", "inactive").execute().data
            bar_md = sum(Decimal(str(c["md_kw"])) for c in circuits)

            circuit_ids = [c["id"] for c in circuits]
            if circuit_ids:
                subs = self.client.table("sub_circuits").select("md_kw").in_("circuit_id", circuit_ids).eq("status", "operative_normal").execute().data
                bar_md += sum(Decimal(str(s["md_kw"])) for s in subs)

            if bar["bar_type"] in ("emergency", "continuity"):
                bar_md *= REDUCED
            total_md += bar_md

        capacity = Decimal(str(station["transformer_capacity_kw"]))
        available = capacity - total_md

        if available < 0:
            status = "red"
        elif capacity > 0:
            status = "yellow" if (available / capacity) < Decimal("0.2") else "green"
        else:
            status = "green"

        updated = self.client.table("stations").update({
            "max_demand_kw": float(total_md),
            "available_power_kw": float(available),
            "status": status,
        }).eq("id", station_id).execute()

        return updated.data[0] if updated.data else station

    def check_capacity(self, bar_id: int, new_md_kw) -> dict:
        bar_result = self.client.table("bars").select("*").eq("id", bar_id).execute()
        if not bar_result.data:
            return {"can_add": False, "message": "Barra no encontrada"}
        bar = bar_result.data[0]

        station_result = self.client.table("stations").select("*").eq("id", bar["station_id"]).execute()
        if not station_result.data:
            return {"can_add": False, "message": "Estacion no encontrada"}
        station = station_result.data[0]

        available = Decimal(str(station["available_power_kw"]))
        new_md = Decimal(str(new_md_kw))
        remaining = available - new_md

        return {
            "can_add": remaining >= 0,
            "available_before": float(available),
            "available_after": float(remaining),
            "station_name": station["name"],
            "message": "Capacidad suficiente" if remaining >= 0 else f"Excede la capacidad disponible por {abs(float(remaining))} kW",
        }

    def get_bar_power_summary(self, bar_id: int) -> dict | None:
        bar_result = self.client.table("bars").select("*").eq("id", bar_id).execute()
        if not bar_result.data:
            return None
        bar = bar_result.data[0]

        circuits = self.client.table("circuits").select("id,pi_kw,md_kw").eq("bar_id", bar_id).neq("status", "inactive").execute().data
        total_pi = sum(Decimal(str(c["pi_kw"])) for c in circuits)
        total_md = sum(Decimal(str(c["md_kw"])) for c in circuits)

        circuit_ids = [c["id"] for c in circuits]
        if circuit_ids:
            subs = self.client.table("sub_circuits").select("pi_kw,md_kw").in_("circuit_id", circuit_ids).eq("status", "operative_normal").execute().data
            total_pi += sum(Decimal(str(s["pi_kw"])) for s in subs)
            total_md += sum(Decimal(str(s["md_kw"])) for s in subs)

        if bar["bar_type"] in ("emergency", "continuity"):
            total_md *= Decimal("0.75")

        capacity_kw = Decimal(str(bar["capacity_kw"]))
        return {
            "total_installed_power_kw": float(total_pi),
            "total_max_demand_kw": float(total_md),
            "max_board_capacity_kw": float(capacity_kw),
            "max_board_capacity_a": float(bar["capacity_a"]),
            "available_power_kw": float(capacity_kw - total_md),
        }
