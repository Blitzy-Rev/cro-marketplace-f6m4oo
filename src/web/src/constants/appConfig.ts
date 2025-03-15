/**
 * appConfig.ts
 * 
 * Central configuration file for the Molecular Data Management and CRO Integration Platform frontend.
 * This file provides application-wide settings derived from environment variables,
 * ensuring consistent configuration across all components.
 */

/**
 * Helper function to safely retrieve environment variables with fallback values
 * @param key - The environment variable key
 * @param defaultValue - Fallback value if the environment variable is not set
 * @returns The environment variable value or the default value
 */
const getEnvVariable = <T>(key: string, defaultValue: T): T => {
  const envVars = import.meta.env as Record<string, string>;
  const value = envVars[key];
  
  if (value === undefined) {
    return defaultValue;
  }
  
  // Handle type conversions based on the default value type
  if (typeof defaultValue === 'number') {
    return Number(value) as unknown as T;
  }
  
  if (typeof defaultValue === 'boolean') {
    return (value === 'true') as unknown as T;
  }
  
  return value as T;
};

/**
 * Type definitions for configuration object
 */
export interface AppConfig {
  app: {
    title: string;
    environment: string;
    version: string;
    buildDate: string;
  };
  api: {
    baseUrl: string;
    timeout: number;
    retryAttempts: number;
    useMocks: boolean;
    websocketUrl: string;
  };
  auth: {
    enabled: boolean;
    tokenStorageKey: string;
    refreshTokenStorageKey: string;
    tokenExpiryStorageKey: string;
  };
  features: {
    aiPrediction: boolean;
    realTimeNotifications: boolean;
    moleculeComparison: boolean;
    batchSubmissions: boolean;
    logging: boolean;
    logLevel: string;
  };
  ui: {
    defaultTheme: string;
    toastDuration: number;
    dashboardRefreshInterval: number;
    defaultPaginationLimit: number;
  };
  molecule: {
    viewerApiKey: string;
    enable3DViewer: boolean;
    defaultViewerMode: string;
    viewerOptions: {
      width: number;
      height: number;
      bondThickness: number;
      atomRadius: number;
      backgroundColor: string;
    };
  };
  limits: {
    maxUploadSize: number;
    maxCsvRows: number;
  };
  integrations: {
    docusign: {
      url: string;
    };
  };
}

/**
 * Main application configuration object
 */
export const APP_CONFIG: AppConfig = {
  /**
   * Basic application information
   */
  app: {
    title: getEnvVariable<string>('VITE_APP_TITLE', 'MoleculeFlow'),
    environment: getEnvVariable<string>('VITE_APP_ENV', 'development'),
    version: getEnvVariable<string>('VITE_APP_VERSION', '1.0.0'),
    buildDate: getEnvVariable<string>('VITE_BUILD_DATE', new Date().toISOString())
  },

  /**
   * API integration settings
   */
  api: {
    baseUrl: getEnvVariable<string>('VITE_API_BASE_URL', ''),
    timeout: getEnvVariable<number>('VITE_API_TIMEOUT', 30000),
    retryAttempts: getEnvVariable<number>('VITE_API_RETRY_ATTEMPTS', 3),
    useMocks: getEnvVariable<boolean>('VITE_MOCK_API', false),
    websocketUrl: getEnvVariable<string>('VITE_WEBSOCKET_URL', '')
  },

  /**
   * Authentication configuration
   */
  auth: {
    enabled: getEnvVariable<boolean>('VITE_AUTH_ENABLED', true),
    tokenStorageKey: getEnvVariable<string>('VITE_TOKEN_STORAGE_KEY', 'auth_token'),
    refreshTokenStorageKey: getEnvVariable<string>('VITE_REFRESH_TOKEN_STORAGE_KEY', 'refresh_token'),
    tokenExpiryStorageKey: getEnvVariable<string>('VITE_TOKEN_EXPIRY_STORAGE_KEY', 'token_expiry')
  },

  /**
   * Feature flags
   */
  features: {
    aiPrediction: getEnvVariable<boolean>('VITE_AI_PREDICTION_ENABLED', true),
    realTimeNotifications: getEnvVariable<boolean>('VITE_ENABLE_REAL_TIME_NOTIFICATIONS', true),
    moleculeComparison: getEnvVariable<boolean>('VITE_ENABLE_MOLECULE_COMPARISON', true),
    batchSubmissions: getEnvVariable<boolean>('VITE_ENABLE_BATCH_SUBMISSIONS', true),
    logging: getEnvVariable<boolean>('VITE_ENABLE_LOGGING', false),
    logLevel: getEnvVariable<string>('VITE_LOG_LEVEL', 'error')
  },

  /**
   * UI/UX settings
   */
  ui: {
    defaultTheme: getEnvVariable<string>('VITE_DEFAULT_THEME', 'light'),
    toastDuration: getEnvVariable<number>('VITE_TOAST_DURATION', 5000),
    dashboardRefreshInterval: getEnvVariable<number>('VITE_DASHBOARD_REFRESH_INTERVAL', 60000),
    defaultPaginationLimit: getEnvVariable<number>('VITE_DEFAULT_PAGINATION_LIMIT', 25)
  },

  /**
   * Molecule visualization settings
   */
  molecule: {
    viewerApiKey: getEnvVariable<string>('VITE_MOLECULE_VIEWER_API_KEY', ''),
    enable3DViewer: getEnvVariable<boolean>('VITE_ENABLE_3D_MOLECULE_VIEWER', true),
    defaultViewerMode: getEnvVariable<string>('VITE_DEFAULT_MOLECULE_VIEWER_MODE', '2D'),
    viewerOptions: {
      width: getEnvVariable<number>('VITE_MOLECULE_VIEWER_WIDTH', 500),
      height: getEnvVariable<number>('VITE_MOLECULE_VIEWER_HEIGHT', 400),
      bondThickness: getEnvVariable<number>('VITE_MOLECULE_VIEWER_BOND_THICKNESS', 1.2),
      atomRadius: getEnvVariable<number>('VITE_MOLECULE_VIEWER_ATOM_RADIUS', 0.8),
      backgroundColor: getEnvVariable<string>('VITE_MOLECULE_VIEWER_BACKGROUND', '#FFFFFF')
    }
  },

  /**
   * System limits
   */
  limits: {
    maxUploadSize: getEnvVariable<number>('VITE_MAX_UPLOAD_SIZE', 104857600), // 100MB
    maxCsvRows: getEnvVariable<number>('VITE_MAX_CSV_ROWS', 500000)
  },

  /**
   * Third-party integrations
   */
  integrations: {
    docusign: {
      url: getEnvVariable<string>('VITE_DOCUSIGN_INTEGRATION_URL', '')
    }
  }
};

export default APP_CONFIG;