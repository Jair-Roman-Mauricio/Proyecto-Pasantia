"""
Módulo de cálculo energético para estaciones eléctricas.

Provee la clase EnergyCalculator, responsable de recalcular la demanda máxima
de una estación, verificar la disponibilidad de capacidad antes de agregar
nuevos circuitos y generar resúmenes de potencia por barra.
"""

from decimal import Decimal
from sqlalchemy.orm import Session
from app.models.station import Station
from app.models.bar import Bar
from app.models.circuit import Circuit
from app.models.sub_circuit import SubCircuit


class EnergyCalculator:
    """
    Calculadora de energía para estaciones eléctricas de la Línea 1 del Metro.

    Encapsula toda la lógica de cálculo de demanda máxima (MD), potencia
    disponible y determinación del estado de color de una estación en función
    de la capacidad restante del transformador.

    Attributes:
        db (Session): Sesión activa de SQLAlchemy utilizada para todas las
            consultas y operaciones de persistencia.
    """

    def __init__(self, db: Session):
        """
        Inicializa el calculador con una sesión de base de datos.

        Args:
            db (Session): Sesión de SQLAlchemy inyectada desde el contexto
                de la solicitud HTTP o del job de fondo.
        """
        self.db = db

    def recalculate_station(self, station_id: int) -> Station:
        """
        Recalcula la demanda máxima total y el estado energético de una estación.

        Suma la MD de todos los circuitos operativos (estado distinto de
        'inactive') de todas las barras de la estación, y adicionalmente
        acumula la MD de los sub-circuitos en estado 'operative_normal'.
        Con ese total determina la potencia disponible y asigna el color
        de estado (green / yellow / red) según los siguientes umbrales:

        - **red**: potencia disponible negativa (la demanda supera la capacidad).
        - **yellow**: potencia disponible menor al 20 % de la capacidad instalada.
        - **green**: potencia disponible mayor o igual al 20 % de la capacidad.

        Args:
            station_id (int): Identificador primario de la estación a recalcular.

        Returns:
            Station: Objeto de estación con los campos ``max_demand_kw``,
                ``available_power_kw`` y ``status`` actualizados y
                persistidos en la base de datos. Retorna ``None`` si la
                estación no existe.
        """
        # Obtener la estación; si no existe, no hay nada que recalcular
        station = self.db.query(Station).filter(Station.id == station_id).first()
        if not station:
            return None

        # Recuperar todas las barras asociadas a la estación
        bars = self.db.query(Bar).filter(Bar.station_id == station_id).all()

        # Factor de reducción aplicado a barras de emergencia y continuidad:
        # su contribución a la demanda total de la estación es el 75 % de su MD acumulada.
        # La barra normal contribuye con el 100 % de su MD.
        REDUCED_DEMAND_FACTOR = Decimal("0.75")

        total_md = Decimal("0")
        for bar in bars:
            # Circuitos activos de esta barra específica
            circuits = (
                self.db.query(Circuit)
                .filter(Circuit.bar_id == bar.id)
                .filter(Circuit.status != "inactive")
                .all()
            )
            bar_md = sum((c.md_kw for c in circuits), Decimal("0"))

            # Sumar la MD de los sub-circuitos operativos de estos circuitos
            circuit_ids = [c.id for c in circuits]
            if circuit_ids:
                sub_circuits = (
                    self.db.query(SubCircuit)
                    .filter(SubCircuit.circuit_id.in_(circuit_ids))
                    .filter(SubCircuit.status == "operative_normal")
                    .all()
                )
                bar_md += sum((s.md_kw for s in sub_circuits), Decimal("0"))

            # Las barras de emergencia y continuidad aportan solo el 75 % de su MD
            if bar.bar_type in ("emergency", "continuity"):
                bar_md *= REDUCED_DEMAND_FACTOR

            total_md += bar_md

        # Actualizar los campos de demanda y potencia disponible en la estación
        station.max_demand_kw = total_md
        station.available_power_kw = station.transformer_capacity_kw - total_md

        # Determinar el color de estado según el porcentaje de capacidad disponible
        if station.available_power_kw < 0:
            # La demanda supera la capacidad instalada del transformador
            station.status = "red"
        elif station.transformer_capacity_kw > 0:
            # Calcular la proporción de capacidad restante respecto al total
            ratio = station.available_power_kw / station.transformer_capacity_kw
            if ratio < Decimal("0.2"):
                # Menos del 20 % de capacidad disponible: alerta amarilla
                station.status = "yellow"
            else:
                # Capacidad suficiente: estado normal verde
                station.status = "green"
        else:
            # Capacidad del transformador en cero; se considera estado normal
            station.status = "green"

        # Persistir los cambios y refrescar el objeto desde la base de datos
        self.db.commit()
        self.db.refresh(station)
        return station

    def check_capacity(self, bar_id: int, new_md_kw: Decimal) -> dict:
        """
        Verifica si agregar una nueva demanda máxima excede la capacidad de la estación.

        Consulta la barra indicada, obtiene su estación asociada y evalúa si
        la potencia disponible actual es suficiente para absorber ``new_md_kw``
        adicionales sin que el balance resulte negativo.

        Args:
            bar_id (int): Identificador primario de la barra a la que se
                desea conectar el nuevo circuito o carga.
            new_md_kw (Decimal): Demanda máxima en kW que se pretende agregar.

        Returns:
            dict: Diccionario con las siguientes claves:
                - ``can_add`` (bool): ``True`` si la capacidad es suficiente.
                - ``available_before`` (float): Potencia disponible actual en kW.
                - ``available_after`` (float): Potencia disponible tras agregar
                  la nueva carga en kW.
                - ``station_name`` (str): Nombre de la estación evaluada.
                - ``message`` (str): Descripción textual del resultado.
                Si la barra no existe, retorna ``{"can_add": False, "message": ...}``.
        """
        # Obtener la barra; si no existe, retornar error inmediatamente
        bar = self.db.query(Bar).filter(Bar.id == bar_id).first()
        if not bar:
            return {"can_add": False, "message": "Barra no encontrada"}

        # Obtener la estación que contiene la barra para leer su potencia disponible
        station = self.db.query(Station).filter(Station.id == bar.station_id).first()

        # Calcular la potencia residual después de agregar la nueva demanda
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
        """
        Retorna un resumen de potencia instalada y demanda máxima de una barra.

        Suma la potencia instalada (PI) y la demanda máxima (MD) de todos los
        circuitos activos de la barra, incluyendo sus sub-circuitos en estado
        operativo normal. También devuelve la capacidad nominal de la barra
        y la potencia disponible calculada como la diferencia entre dicha
        capacidad y la MD total.

        Args:
            bar_id (int): Identificador primario de la barra consultada.

        Returns:
            dict: Diccionario con las siguientes claves:
                - ``total_installed_power_kw`` (float): Suma de PI de circuitos
                  y sub-circuitos en kW.
                - ``total_max_demand_kw`` (float): Suma de MD en kW.
                - ``max_board_capacity_kw`` (float): Capacidad nominal de la
                  barra en kW.
                - ``max_board_capacity_a`` (float): Capacidad nominal de la
                  barra en amperios.
                - ``available_power_kw`` (float): Capacidad nominal menos la
                  MD total en kW.
                Retorna ``None`` si la barra no existe.
        """
        # Obtener la barra; si no existe, retornar None
        bar = self.db.query(Bar).filter(Bar.id == bar_id).first()
        if not bar:
            return None

        # Consultar circuitos activos u operativos de esta barra específica
        circuits = (
            self.db.query(Circuit)
            .filter(Circuit.bar_id == bar_id, Circuit.status != "inactive")
            .all()
        )

        # Acumular potencia instalada y demanda máxima de los circuitos directos
        total_pi = sum((c.pi_kw for c in circuits), Decimal("0"))
        total_md = sum((c.md_kw for c in circuits), Decimal("0"))

        # Sumar también la PI y MD de los sub-circuitos operativos
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

        # Las barras de emergencia y continuidad aplican un factor de 0.75 sobre la MD total.
        # La potencia instalada (PI) no se reduce: refleja lo físicamente instalado.
        if bar.bar_type in ("emergency", "continuity"):
            total_md *= Decimal("0.75")

        return {
            "total_installed_power_kw": float(total_pi),
            "total_max_demand_kw": float(total_md),
            "max_board_capacity_kw": float(bar.capacity_kw),
            "max_board_capacity_a": float(bar.capacity_a),
            "available_power_kw": float(bar.capacity_kw - total_md),
        }
