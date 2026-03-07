# Guía de Usuario — OPERSAC (Operador de Servicio)

## ¿Qué puede hacer el OPERSAC?

El rol **opersac** tiene acceso limitado al sistema, controlado por los permisos que el administrador le asigne. Las funcionalidades disponibles dependerán de los permisos habilitados.

---

## 1. Ver el Mapa de Línea 1

*(Requiere permiso: `view_stations`)*

Al ingresar, el mapa muestra las 26 estaciones de la Línea 1 con código de colores:

| Color | Significado |
|-------|-------------|
| 🟢 Verde | Capacidad suficiente |
| 🟡 Amarillo | Menos del 20% disponible |
| 🔴 Rojo | Sobrecargada |

**Clic en una estación** muestra el detalle energético:
- Capacidad del transformador
- Demanda máxima actual
- Potencia disponible
- Estado de cada barra (normal, emergencia, continuidad)

Si también tiene el permiso `view_circuits`, puede ver los circuitos de cada barra y sus sub-circuitos.

---

## 2. Enviar una Solicitud de Ampliación

*(Requiere permiso: `send_requests`)*

Cuando necesita conectar nueva carga eléctrica en una estación, debe enviar una solicitud al administrador.

### Pasos para crear una solicitud:

1. Ir a **Mis Solicitudes** en el menú lateral
2. Clic en **"Nueva Solicitud"**
3. Completar el formulario:

   **Datos de ubicación:**
   - **Estación:** seleccionar la estación donde se instalará
   - **Tipo de barra:** normal, emergencia o continuidad

   **Tipo de solicitud:**
   - **Nuevo circuito:** si el equipo/local necesita un circuito propio
   - **Ampliación de circuito existente:** si se agrega un punto más a un circuito ya existente

   **Datos de carga:**
   - **Carga solicitada (kW):** potencia instalada del equipo
   - **Factor de demanda:** estimado de uso real (0.1 a 1.0)
   - **Local/ítem:** identificación del local o equipo

   **Justificación:** describir el motivo de la ampliación (requerido)

4. Clic en **"Enviar Solicitud"**

La solicitud queda en estado **Pendiente** hasta que el administrador la revise.

---

## 3. Seguimiento de Mis Solicitudes

*(Requiere permiso: `send_requests`)*

En **Mis Solicitudes** puede ver el historial de todas sus solicitudes y su estado actual:

| Estado | Descripción |
|--------|-------------|
| 🟡 Pendiente | En espera de revisión por el administrador |
| 🟢 Aprobada | El circuito/sub-circuito fue creado en el sistema |
| 🔴 Rechazada | La solicitud fue denegada (ver motivo) |

Si una solicitud es rechazada, puede ver el **motivo del rechazo** para corregir y enviar una nueva solicitud si corresponde.

---

## 4. Agregar Observaciones

*(Requiere permiso: `add_observations`)*

Puede registrar observaciones técnicas sobre la infraestructura eléctrica.

### Tipos de observación:

| Severidad | Cuándo usar |
|-----------|-------------|
| 🔴 Urgente | Peligro inmediato, requiere atención ahora |
| 🟡 Advertencia | Situación anómala que debe monitorearse |
| 🔵 Recomendación | Mejora sugerida, sin urgencia |

### Cómo agregar una observación:
1. Ir al detalle de una estación → seleccionar circuito o barra
2. Clic en **"Observaciones"**
3. Clic en **"Nueva Observación"**
4. Seleccionar severidad y escribir el contenido
5. Guardar

Las observaciones quedan visibles para todos los usuarios autenticados y el administrador puede eliminarlas si corresponde.

---

## 5. Ver Reportes

*(Requiere permiso: `view_reports`)*

En **Reportes** puede consultar:

### Demanda eléctrica
Muestra la capacidad, demanda máxima y potencia disponible de cada estación.
- Sin filtro de fechas: valores actuales
- Con filtro de fechas: carga acumulada de circuitos creados en ese período

### Solicitudes por estación
Muestra cuántas solicitudes hay por estación, separadas por estado (pendientes, aprobadas, rechazadas).

### Exportar a Excel
Descarga los reportes en formato Excel con gráficos incluidos (línea de demanda y barras de solicitudes).

---

## Preguntas frecuentes

**¿Por qué no veo algunas opciones del menú?**
Los permisos son asignados por el administrador. Si necesita acceso a una funcionalidad, solicítelo a su administrador del sistema.

**¿Mi solicitud puede ser rechazada?**
Sí, el administrador evalúa la disponibilidad de capacidad en la estación y la justificación técnica. Si es rechazada, el motivo quedará registrado en la solicitud.

**¿Puedo ver los circuitos sin tener `view_circuits`?**
Solo verá la información de barras y estaciones. Los circuitos y sub-circuitos requieren el permiso específico.

**¿Qué pasa después de que se aprueba mi solicitud?**
El sistema crea automáticamente el circuito o sub-circuito en la estación indicada. El estado de su solicitud cambia a "Aprobada".
