# Excel Export con Graficos Embebidos

## Contexto
El boton "Exportar Excel" en Reportes no funciona correctamente para usuarios no-admin (usa `require_admin` pero el boton es visible para todos). Ademas, el usuario quiere que el Excel incluya graficos embebidos (no solo tablas de datos), y que los datos dependan del filtro de fechas.

## Cambios

### 1. Backend: Reescribir endpoint de exportacion
**`backend/app/api/v1/reports.py`** - endpoint `GET /export/excel`:

- Cambiar `require_admin` a `check_permission("view_reports")` para que Opersac tambien pueda exportar
- Aplicar filtro de fechas a Sheet 1 (Demanda Electrica) igual que en el endpoint `/demand-evolution`
- Agregar graficos embebidos con `openpyxl.chart`:
  - **Sheet 1 "Demanda Electrica"**: Tabla de datos + `LineChart` con dos series (Demanda Real en rojo, Capacidad Maxima en verde punteado)
  - **Sheet 2 "Solicitudes por Estacion"**: Tabla de datos + `BarChart` con tres series (Pendientes amarillo, Aprobadas verde, Rechazadas rojo)
- Ajustar anchos de columna para legibilidad
- Los graficos se colocan debajo de las tablas de datos

### 2. Frontend: Agregar manejo de errores
**`frontend/src/components/reports/ReportsView.tsx`** - funcion `handleExport`:

- Envolver en try/catch
- Mostrar alert si falla la descarga

## Archivos a modificar
1. `backend/app/api/v1/reports.py` — reescribir `export_reports_excel`
2. `frontend/src/components/reports/ReportsView.tsx` — agregar try/catch a `handleExport`

## Verificacion
1. Iniciar sesion como admin, ir a Reportes, click "Exportar Excel" sin filtros — debe descargar Excel con graficos
2. Aplicar filtro de fechas, exportar — datos y graficos deben reflejar el periodo filtrado
3. Iniciar sesion como Opersac con permiso `view_reports` — debe poder exportar tambien
4. Abrir el Excel en Excel/LibreOffice — verificar que los graficos se renderizan correctamente
