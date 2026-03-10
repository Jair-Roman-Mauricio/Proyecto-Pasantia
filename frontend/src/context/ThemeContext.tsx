import { createContext, useContext, useState, useEffect, type ReactNode } from 'react';

/**
 * Temas visuales disponibles en la aplicación.
 * - `'light'` - Tema claro (predeterminado).
 * - `'dark'`  - Tema oscuro.
 */
type Theme = 'light' | 'dark';

/**
 * Contrato del contexto de tema visual.
 *
 * @property theme       - Tema actualmente aplicado (`'light'` o `'dark'`).
 * @property toggleTheme - Alterna entre el tema claro y oscuro, y persiste la preferencia en localStorage.
 */
interface ThemeContextType {
  theme: Theme;
  toggleTheme: () => void;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

export function ThemeProvider({ children }: { children: ReactNode }) {
  // Inicialización perezosa: recupera el tema persistido en localStorage al montar el proveedor.
  // Si no existe una preferencia guardada, se usa 'light' como valor por defecto.
  const [theme, setTheme] = useState<Theme>(() => {
    return (localStorage.getItem('theme') as Theme) || 'light';
  });

  /**
   * Efecto de sincronización: cada vez que cambia el tema se aplica o elimina la clase
   * `dark` en el elemento raíz del documento (necesario para Tailwind CSS dark mode),
   * y se persiste la nueva preferencia en localStorage para que se restaure en la próxima sesión.
   */
  useEffect(() => {
    const root = document.documentElement;
    if (theme === 'dark') {
      root.classList.add('dark');
    } else {
      root.classList.remove('dark');
    }
    // Persiste el tema seleccionado para restaurarlo automáticamente al recargar la página
    localStorage.setItem('theme', theme);
  }, [theme]);

  /**
   * Alterna el tema entre `'light'` y `'dark'`.
   * El cambio se propaga al DOM y se guarda en localStorage a través del efecto anterior.
   */
  const toggleTheme = () => {
    setTheme((prev) => (prev === 'light' ? 'dark' : 'light'));
  };

  return (
    <ThemeContext.Provider value={{ theme, toggleTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}

/**
 * Hook para consumir el contexto de tema desde cualquier componente hijo de `ThemeProvider`.
 *
 * @throws {Error} Si se utiliza fuera del árbol de `ThemeProvider`.
 * @returns El valor completo del contexto de tema (`ThemeContextType`).
 *
 * @example
 * const { theme, toggleTheme } = useTheme();
 */
export function useTheme() {
  const context = useContext(ThemeContext);
  if (!context) throw new Error('useTheme must be used within ThemeProvider');
  return context;
}
