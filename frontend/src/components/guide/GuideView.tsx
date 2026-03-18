/**
 * Vista del manual de usuario del sistema.
 * Muestra un conjunto de secciones con pasos numerados adaptado al rol del usuario:
 *  - Admin:   cubre mapa, gestión de circuitos, solicitudes, notificaciones, backup, auditoría y reportes.
 *  - Opersac: cubre mapa, solicitudes propias y reportes.
 * En pantallas pequeñas la navegación usa un selector desplegable; en desktop usa un sidebar.
 */
import { useState } from 'react';
import { useAuth } from '../../context/AuthContext';

/** Estructura de una sección del manual con sus pasos */
interface Section {
  id: string;
  title: string;
  steps: { heading: string; text: string }[];
}

const adminSections: Section[] = [
  {
    id: 'map',
    title: 'Mapa de Linea 1',
    steps: [
      { heading: 'Ver el estado de las estaciones', text: 'En el mapa SVG cada nodo representa una estacion. El color indica el estado energetico: verde (energia suficiente), amarillo (menos del 20% disponible) y rojo (debe energia).' },
      { heading: 'Abrir detalle de estacion', text: 'Haz click sobre cualquier nodo para abrir el panel lateral derecho. Ahi veras la demanda maxima, potencia disponible y el grafico de consumo.' },
      { heading: 'Navegar al detalle completo', text: 'Desde el panel lateral, haz click en "Ver detalle completo" para ir a la pagina de la estacion con barras, circuitos y mapa unifilar.' },
    ],
  },
  {
    id: 'circuits',
    title: 'Gestion de Circuitos',
    steps: [
      { heading: 'Acceder a una estacion', text: 'Desde el mapa, haz click en una estacion y luego en "Ver detalle completo". Selecciona la pestaña "Barras y Circuitos".' },
      { heading: 'Crear un circuito', text: 'En la barra correspondiente (normal, emergencia, continuidad) haz click en "+ Agregar Circuito". Completa denominacion, nombre, PI (kW) y FD. La MD se calcula automaticamente.' },
      { heading: 'Exceder capacidad', text: 'Si la carga supera la capacidad disponible, el sistema mostrara una advertencia con el detalle. Puedes confirmar con "Forzar" para agregarlo de todas formas.' },
      { heading: 'Cambiar estado', text: 'En la tabla de circuitos, usa el boton de estado para cambiar entre Operativo, Reserva R, Reserva RE e Inactivo. Reserva requiere una fecha de expiracion.' },
      { heading: 'Eliminar circuito', text: 'Haz click en el icono de eliminacion. La accion es irreversible y recalculara la energia de la estacion.' },
    ],
  },
  {
    id: 'requests',
    title: 'Solicitudes de Opersac',
    steps: [
      { heading: 'Ver solicitudes pendientes', text: 'En el menu lateral selecciona "Solicitudes". La tabla muestra todas las solicitudes ordenadas por fecha, con su estado (pendiente, aprobada, rechazada).' },
      { heading: 'Aprobar una solicitud', text: 'Haz click en el boton "Aprobar". El sistema creara automaticamente el circuito o sub-circuito solicitado y recalculara la energia.' },
      { heading: 'Rechazar una solicitud', text: 'Haz click en "Rechazar" e ingresa el motivo. El opersac podra ver el motivo desde su perfil.' },
    ],
  },
  {
    id: 'notifications',
    title: 'Notificaciones',
    steps: [
      { heading: 'Tipos de notificacion', text: 'El sistema genera notificaciones automaticas para: circuitos en reserva proximos a vencer (sin contacto con el cliente) y estaciones con energia negativa.' },
      { heading: 'Marcar como leida', text: 'Haz click en el icono de check para marcar una notificacion como leida. Esto no elimina la notificacion.' },
      { heading: 'Extender reserva', text: 'Para notificaciones de tipo "reserva sin contacto", puedes extender la fecha de vencimiento haciendo click en "Extender".' },
      { heading: 'Resolver reserva', text: 'Si el circuito ya no se necesita en reserva, usa "Resolver" para cambiar su estado a Inactivo y cerrar la notificacion.' },
    ],
  },
  {
    id: 'users',
    title: 'Gestion de Usuarios',
    steps: [
      { heading: 'Crear usuario', text: 'En "Gestion de Usuarios" haz click en "+ Nuevo Usuario". Selecciona el rol: Admin (acceso total) u Opersac (acceso segun permisos).' },
      { heading: 'Gestionar permisos Opersac', text: 'En "Permisos", selecciona un usuario Opersac y activa o desactiva cada permiso: ver estaciones, enviar solicitudes, ver reportes.' },
    ],
  },
  {
    id: 'backup',
    title: 'Backup y Exportacion',
    steps: [
      { heading: 'Crear backup', text: 'En "Backup" haz click en "Crear Backup". El sistema guardara una instantanea de todos los datos en la base de datos.' },
      { heading: 'Descargar como JSON', text: 'Cada backup tiene un boton "Descargar" que exporta los datos en formato JSON para guardar externamente.' },
      { heading: 'Exportar pg_dump', text: 'El boton "Exportar pg_dump" genera un volcado completo de la base de datos PostgreSQL. Util para migraciones y backups de produccion.' },
      { heading: 'Restaurar backup', text: 'Haz click en "Restaurar" en cualquier backup para volver al estado de datos de ese momento. Esta accion sobreescribe los datos actuales.' },
    ],
  },
  {
    id: 'audit',
    title: 'Auditoria',
    steps: [
      { heading: 'Ver historial de acciones', text: 'En "Auditoria" se registran todas las acciones del sistema: creacion, edicion y eliminacion de circuitos, usuarios, solicitudes y backups.' },
      { heading: 'Filtrar logs', text: 'Usa los filtros por tipo de entidad, usuario, accion o rango de fechas para encontrar eventos especificos.' },
    ],
  },
  {
    id: 'reports',
    title: 'Reportes',
    steps: [
      { heading: 'Ver demanda por estacion', text: 'El grafico superior muestra la demanda actual vs la energia disponible para una estacion. Usa el selector para cambiar de estacion.' },
      { heading: 'Ver solicitudes por estacion', text: 'El grafico inferior agrupa las solicitudes de Opersac por estacion, mostrando cuantas estan pendientes, aprobadas y rechazadas.' },
      { heading: 'Filtrar por fechas', text: 'Usa los campos de fecha inicio y fin para filtrar ambos graficos. Sin fechas, se muestran los datos actuales.' },
      { heading: 'Exportar Excel', text: 'El boton "Exportar Excel" descarga un archivo con tablas y graficos embebidos para ambas vistas.' },
    ],
  },
];

const opersacSections: Section[] = [
  {
    id: 'map',
    title: 'Mapa de Linea 1',
    steps: [
      { heading: 'Ver estaciones', text: 'El mapa muestra las 26 estaciones de la Linea 1. El color del nodo indica el estado energetico: verde (normal), amarillo (critico) o rojo (sobrecargado).' },
      { heading: 'Ver detalle', text: 'Haz click en cualquier estacion para ver su demanda actual, potencia disponible y un grafico de consumo en el panel lateral.' },
    ],
  },
  {
    id: 'requests',
    title: 'Mis Solicitudes',
    steps: [
      { heading: 'Crear una solicitud', text: 'En "Mis Solicitudes" haz click en "+ Nueva Solicitud". Selecciona la estacion, tipo de barra y la carga requerida en kW.' },
      { heading: 'Tipos de solicitud', text: 'Puedes solicitar un nuevo circuito (sin seleccionar circuito existente) o un sub-circuito dentro de un circuito ya existente.' },
      { heading: 'Seguimiento', text: 'Tus solicitudes aparecen en la tabla con su estado: Pendiente (en revision), Aprobada (creada en el sistema) o Rechazada (con motivo del admin).' },
    ],
  },
  {
    id: 'reports',
    title: 'Reportes',
    steps: [
      { heading: 'Ver graficos', text: 'En "Reportes" puedes ver la demanda electrica por estacion y el historial de solicitudes. Usa el filtro de fechas para acotar el periodo.' },
      { heading: 'Exportar', text: 'Si tienes el permiso correspondiente, el boton "Exportar Excel" descarga un archivo con los datos y graficos del periodo seleccionado.' },
    ],
  },
];

export default function GuideView() {
  const { user } = useAuth();
  const isAdmin = user?.role === 'admin';
  // Selecciona el conjunto de secciones adecuado según el rol del usuario autenticado
  const sections = isAdmin ? adminSections : opersacSections;
  const [activeSection, setActiveSection] = useState(sections[0].id);

  // Fallback a la primera sección si la activa no se encuentra (ej. cambio de rol)
  const current = sections.find((s) => s.id === activeSection) ?? sections[0];

  return (
    <div className="flex flex-col sm:flex-row gap-0 min-h-[600px]">
      {/* Navegación móvil: selector desplegable */}
      <div className="sm:hidden px-1 pb-4">
        <p className="text-xs font-semibold text-[var(--text-muted)] uppercase tracking-wider mb-2">
          {isAdmin ? 'Manual Admin' : 'Manual Opersac'}
        </p>
        <select
          value={activeSection}
          onChange={(e) => setActiveSection(e.target.value)}
          className="w-full px-3 py-2 rounded-lg border border-[var(--border-color)] bg-[var(--bg-primary)] text-[var(--text-primary)] text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
        >
          {sections.map((s) => (
            <option key={s.id} value={s.id}>{s.title}</option>
          ))}
        </select>
      </div>

      {/* Sidebar nav — solo visible en sm+ */}
      <aside className="hidden sm:block w-52 shrink-0 border-r border-[var(--border-color)] py-2">
        <p className="px-4 text-xs font-semibold text-[var(--text-muted)] uppercase tracking-wider mb-2">
          {isAdmin ? 'Manual Admin' : 'Manual Opersac'}
        </p>
        <nav>
          {sections.map((s) => (
            <button
              key={s.id}
              onClick={() => setActiveSection(s.id)}
              className={`w-full text-left px-4 py-2 text-sm transition-colors cursor-pointer rounded-r-lg border-l-2 ${
                activeSection === s.id
                  ? 'border-primary-500 bg-primary-600/10 text-primary-400 font-medium'
                  : 'border-transparent text-[var(--text-secondary)] hover:bg-[var(--hover-bg)]'
              }`}
            >
              {s.title}
            </button>
          ))}
        </nav>
      </aside>

      {/* Contenido */}
      <div className="flex-1 px-2 sm:px-8 py-4 max-w-2xl">
        <h2 className="text-xl font-bold text-[var(--text-primary)] mb-1">{current.title}</h2>
        <div className="w-10 h-0.5 bg-primary-500 mb-6 rounded-full" />

        <div className="space-y-6">
          {current.steps.map((step, i) => (
            <div key={i} className="flex gap-4">
              <div className="shrink-0 w-7 h-7 rounded-full bg-primary-600/20 text-primary-400 flex items-center justify-center text-xs font-bold">
                {i + 1}
              </div>
              <div>
                <p className="text-sm font-semibold text-[var(--text-primary)] mb-0.5">{step.heading}</p>
                <p className="text-sm text-[var(--text-secondary)] leading-relaxed">{step.text}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
