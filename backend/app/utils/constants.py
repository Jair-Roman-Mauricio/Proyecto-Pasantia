# Lista de las 26 estaciones de la Línea 1 del Metro de Lima,
# ordenadas de sur a norte (Villa El Salvador → Bayóvar).
# Cada entrada define el código único, el nombre oficial y el índice de orden para visualización.
STATIONS = [
    {"code": "E01", "name": "Villa El Salvador", "order_index": 1},
    {"code": "E02", "name": "Parque Industrial", "order_index": 2},
    {"code": "E03", "name": "Pumacahua", "order_index": 3},
    {"code": "E04", "name": "Villa Maria", "order_index": 4},
    {"code": "E05", "name": "Maria Auxiliadora", "order_index": 5},
    {"code": "E06", "name": "San Juan", "order_index": 6},
    {"code": "E07", "name": "Atocongo", "order_index": 7},
    {"code": "E08", "name": "Jorge Chavez", "order_index": 8},
    {"code": "E09", "name": "Ayacucho", "order_index": 9},
    {"code": "E10", "name": "Cabitos", "order_index": 10},
    {"code": "E11", "name": "Angamos", "order_index": 11},
    {"code": "E12", "name": "San Borja Sur", "order_index": 12},
    {"code": "E13", "name": "La Cultura", "order_index": 13},
    {"code": "E14", "name": "Arriola", "order_index": 14},
    {"code": "E15", "name": "Gamarra", "order_index": 15},
    {"code": "E16", "name": "Miguel Grau", "order_index": 16},
    {"code": "E17", "name": "El Angel", "order_index": 17},
    {"code": "E18", "name": "Presbitero Maestro", "order_index": 18},
    {"code": "E19", "name": "Caja de Agua", "order_index": 19},
    {"code": "E20", "name": "Piramide del Sol", "order_index": 20},
    {"code": "E21", "name": "Los Jardines", "order_index": 21},
    {"code": "E22", "name": "Los Postes", "order_index": 22},
    {"code": "E23", "name": "San Carlos", "order_index": 23},
    {"code": "E24", "name": "San Martin", "order_index": 24},
    {"code": "E25", "name": "Santa Rosa", "order_index": 25},
    {"code": "E26", "name": "Bayovar", "order_index": 26},
]

# Tipos de barra eléctrica que se crean automáticamente en cada estación al iniciar.
# Cada estación tiene exactamente una barra de cada tipo.
BAR_TYPES = [
    {"name": "Barra Normal", "bar_type": "normal"},
    {"name": "Barra Emergencia", "bar_type": "emergency"},
    {"name": "Barra Continuidad", "bar_type": "continuity"},
]

# Claves de permiso disponibles para usuarios con rol OPERSAC.
# El admin gestiona cuáles están habilitadas por usuario en la tabla permissions.
PERMISSION_FEATURES = [
    "view_stations",    # Ver estaciones, barras y circuitos
    "view_circuits",    # Ver detalles de circuitos y sub-circuitos
    "send_requests",    # Enviar solicitudes de ampliación de carga
    "add_observations", # Agregar observaciones técnicas a la infraestructura
    "view_reports",     # Acceder a reportes y exportación Excel
]

# Motivos predefinidos para justificar cambios de imagen en estaciones, barras o circuitos.
# El usuario puede seleccionar uno de estos valores en el formulario o elegir "Otro".
IMAGE_JUSTIFICATION_REASONS = [
    "Actualizacion de infraestructura",
    "Correccion de imagen",
    "Revision periodica",
    "Mantenimiento realizado",
    "Cambio de equipo",
    "Otro",
]
