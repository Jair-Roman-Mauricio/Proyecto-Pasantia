/**
 * Punto de entrada de la aplicación React.
 * Monta el componente raíz App dentro de StrictMode para detectar efectos secundarios
 * involuntarios en el entorno de desarrollo (doble invocación de efectos y renders).
 */
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'

// El operador non-null (!) es seguro aquí porque el elemento 'root' siempre existe en index.html
createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
