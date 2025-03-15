import { defineConfig } from 'vite'; // ^4.4.7
import react from '@vitejs/plugin-react'; // ^4.0.4
import checker from 'vite-plugin-checker'; // ^0.6.1
import tsconfigPaths from 'vite-tsconfig-paths'; // ^4.2.0
import svgr from 'vite-plugin-svgr'; // ^3.2.0
import path from 'path'; // built-in
import process from 'node:process';

/**
 * Helper function to load environment variables based on mode
 * @param mode - The current mode (development, production, test)
 * @returns Environment variables object with custom processing
 */
const loadEnv = (mode: string) => {
  try {
    // Base environment variables
    const envDefaults = {
      VITE_APP_MODE: mode,
      VITE_APP_API_BASE_URL: mode === 'production' ? '/api' : 'http://localhost:8000/api',
    };
    
    // Merge with any mode-specific variables from process.env
    const modeEnv = process.env || {};
    
    // Return combined environment variables with defaults
    return {
      ...envDefaults,
      ...modeEnv,
    };
  } catch (error) {
    console.error('Error loading environment variables:', error);
    return { VITE_APP_MODE: mode };
  }
};

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode);
  const isProd = mode === 'production';

  return {
    root: process.cwd(),
    base: '/',
    plugins: [
      // Enable React with Fast Refresh for development
      react(),
      
      // TypeScript type checking during development
      checker({ 
        typescript: true,
        eslint: {
          lintCommand: 'eslint "./src/**/*.{ts,tsx}"'
        }
      }),
      
      // Support for TypeScript path aliases defined in tsconfig.json
      tsconfigPaths(),
      
      // Transform SVGs into React components (import Logo from './logo.svg?react')
      svgr(),
    ],
    
    resolve: {
      alias: {
        '@': path.resolve(__dirname, './src'), // Path alias for src directory
      },
    },
    
    server: {
      port: 3000,
      open: true, // Automatically open browser on server start
      proxy: {
        '/api': {
          target: 'http://localhost:8000',
          changeOrigin: true,
        },
      },
      // Watch for changes in node_modules for local package development
      watch: {
        ignored: ['!**/node_modules/chemdoodle-web/**'],
      },
    },
    
    build: {
      outDir: 'dist',
      sourcemap: !isProd, // Source maps in development and staging only
      minify: isProd ? 'terser' : false,
      terserOptions: isProd ? {
        compress: {
          drop_console: true,
          drop_debugger: true,
        },
        mangle: true,
      } : undefined,
      rollupOptions: {
        output: {
          manualChunks: {
            // Split vendor libraries for better caching
            vendor: [
              'react', 
              'react-dom', 
              'react-router-dom',
              '@mui/material',
              '@emotion/react',
              '@emotion/styled'
            ],
            // Molecular visualization libraries (tend to be large)
            'molecule-viewer': [
              'chemdoodle-web',
              'd3'
            ],
            // State management and data fetching
            'data-management': [
              'redux',
              '@reduxjs/toolkit',
              'react-query',
              'axios'
            ],
          },
        },
      },
      // Limit chunk size warnings
      chunkSizeWarningLimit: 1000,
    },
    
    test: {
      globals: true,
      environment: 'jsdom',
      setupFiles: ['src/setupTests.ts'],
      coverage: {
        reporter: ['text', 'json', 'html'],
        exclude: ['node_modules/', 'src/setupTests.ts'],
      },
    },
    
    define: {
      // Global constants available in the app
      __APP_VERSION__: JSON.stringify(process.env.npm_package_version),
      __BUILD_TIME__: JSON.stringify(new Date().toISOString()),
      __DEV_MODE__: JSON.stringify(!isProd),
    },
    
    optimizeDeps: {
      include: [
        'react',
        'react-dom',
        'react-router-dom',
        '@mui/material',
        '@reduxjs/toolkit',
        'react-query',
        'lodash',
      ],
      exclude: [
        // Exclude problematic dependencies that should be loaded as-is
        'chemdoodle-web'
      ],
    },
    
    // Environment variables that should be available to client
    envPrefix: 'VITE_',
  };
});