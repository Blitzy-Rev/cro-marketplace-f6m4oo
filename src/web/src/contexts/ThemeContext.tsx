import { createContext, useContext, useState, useEffect, useCallback, ReactNode } from 'react'; // react ^18.0.0
import { ThemeProvider as MuiThemeProvider, Theme } from '@mui/material/styles'; // @mui/material/styles ^5.0.0
import { useMediaQuery } from '@mui/material'; // @mui/material ^5.0.0
import { lightTheme, darkTheme } from '../assets/theme';
import { getItem, setItem } from '../utils/localStorage';

// Key for storing theme preference in localStorage
const THEME_STORAGE_KEY = 'theme_preference';

/**
 * Interface defining the shape of the theme context
 */
interface ThemeContextType {
  /** Current theme mode ('light' or 'dark') */
  mode: string;
  /** Current theme object */
  theme: Theme;
  /** Function to toggle between light and dark modes */
  toggleTheme: () => void;
  /** Function to set a specific theme mode */
  setThemeMode: (mode: string) => void;
}

/**
 * React context for theme state and functions
 */
const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

/**
 * Theme provider component that manages theme state
 */
const ThemeProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  // State for theme mode and theme object
  const [mode, setMode] = useState<string>('light');
  const [theme, setTheme] = useState<Theme>(lightTheme);

  // Check system theme preference using media query
  const prefersDarkMode = useMediaQuery('(prefers-color-scheme: dark)');

  // Initialize theme from localStorage or system preference
  useEffect(() => {
    // Try to get saved theme preference from localStorage
    const savedTheme = getItem<string>(THEME_STORAGE_KEY);
    
    if (savedTheme && (savedTheme === 'light' || savedTheme === 'dark')) {
      // Use saved preference if valid
      setMode(savedTheme);
      setTheme(savedTheme === 'dark' ? darkTheme : lightTheme);
    } else {
      // Fall back to system preference if no valid saved preference
      const systemPreferredMode = prefersDarkMode ? 'dark' : 'light';
      setMode(systemPreferredMode);
      setTheme(systemPreferredMode === 'dark' ? darkTheme : lightTheme);
      
      // Save system preference to localStorage
      setItem(THEME_STORAGE_KEY, systemPreferredMode);
    }
  }, [prefersDarkMode]);

  /**
   * Toggles between light and dark theme modes
   */
  const toggleTheme = useCallback(() => {
    const newMode = mode === 'light' ? 'dark' : 'light';
    setMode(newMode);
    setTheme(newMode === 'dark' ? darkTheme : lightTheme);
    setItem(THEME_STORAGE_KEY, newMode);
  }, [mode]);

  /**
   * Sets the theme mode to a specific value
   */
  const setThemeMode = useCallback((newMode: string) => {
    if (newMode !== 'light' && newMode !== 'dark') {
      console.error('Invalid theme mode. Must be "light" or "dark".');
      return;
    }
    
    setMode(newMode);
    setTheme(newMode === 'dark' ? darkTheme : lightTheme);
    setItem(THEME_STORAGE_KEY, newMode);
  }, []);

  // Construct the context value object
  const contextValue: ThemeContextType = {
    mode,
    theme,
    toggleTheme,
    setThemeMode
  };

  // Render the providers with children
  return (
    <ThemeContext.Provider value={contextValue}>
      <MuiThemeProvider theme={theme}>
        {children}
      </MuiThemeProvider>
    </ThemeContext.Provider>
  );
};

/**
 * Custom hook that provides access to the theme context
 * @returns Theme context containing state and functions
 * @throws Error if used outside ThemeProvider
 */
const useThemeContext = (): ThemeContextType => {
  const context = useContext(ThemeContext);
  
  if (context === undefined) {
    throw new Error('useThemeContext must be used within a ThemeProvider');
  }
  
  return context;
};

export { ThemeContext, ThemeProvider, useThemeContext };