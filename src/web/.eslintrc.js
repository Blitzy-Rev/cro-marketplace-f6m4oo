module.exports = {
  root: true,
  parser: '@typescript-eslint/parser', // @typescript-eslint/parser version ^6.2.1
  parserOptions: {
    ecmaVersion: 2020,
    sourceType: 'module',
    ecmaFeatures: {
      jsx: true,
    },
    project: './tsconfig.json',
  },
  extends: [
    'eslint:recommended',
    'plugin:@typescript-eslint/recommended', // @typescript-eslint/eslint-plugin version ^6.2.1
    'plugin:react/recommended', // eslint-plugin-react version ^7.33.1
    'plugin:react-hooks/recommended', // eslint-plugin-react-hooks version ^4.6.0
    'plugin:jsx-a11y/recommended', // eslint-plugin-jsx-a11y version ^6.7.1
    'plugin:import/errors', // eslint-plugin-import version ^2.28.0
    'plugin:import/warnings',
    'plugin:import/typescript',
    'plugin:jest/recommended', // eslint-plugin-jest version ^27.2.3
    'prettier', // eslint-config-prettier version ^8.10.0
  ],
  plugins: [
    '@typescript-eslint',
    'react',
    'react-hooks',
    'jsx-a11y',
    'import',
    'jest',
  ],
  env: {
    browser: true,
    node: true,
    es6: true,
    jest: true,
  },
  settings: {
    react: {
      version: 'detect',
    },
    'import/resolver': {
      typescript: {
        alwaysTryTypes: true,
        project: './tsconfig.json',
      },
      node: {
        extensions: ['.js', '.jsx', '.ts', '.tsx'],
      },
    },
  },
  rules: {
    // General rules
    'no-console': ['warn', { allow: ['warn', 'error', 'info'] }],
    'no-unused-vars': 'off',
    '@typescript-eslint/no-unused-vars': ['error', { argsIgnorePattern: '^_', varsIgnorePattern: '^_' }],
    '@typescript-eslint/explicit-function-return-type': 'off',
    '@typescript-eslint/explicit-module-boundary-types': 'off',
    '@typescript-eslint/no-explicit-any': 'warn',
    
    // React specific rules
    'react/prop-types': 'off', // Not needed with TypeScript
    'react/react-in-jsx-scope': 'off', // Not needed with React 17+
    'react-hooks/rules-of-hooks': 'error',
    'react-hooks/exhaustive-deps': 'warn',
    
    // Import ordering
    'import/order': [
      'error',
      {
        groups: ['builtin', 'external', 'internal', 'parent', 'sibling', 'index'],
        'newlines-between': 'always',
        alphabetize: {
          order: 'asc',
          caseInsensitive: true,
        },
      },
    ],
    
    // Accessibility rules
    'jsx-a11y/anchor-is-valid': [
      'error',
      {
        components: ['Link'],
        specialLink: ['to'],
      },
    ],
    
    // Jest rules
    'jest/no-disabled-tests': 'warn',
    'jest/no-focused-tests': 'error',
    'jest/prefer-to-have-length': 'warn',
  },
  overrides: [
    // Special rules for test files
    {
      files: ['**/*.test.ts', '**/*.test.tsx'],
      env: {
        jest: true,
      },
      rules: {
        '@typescript-eslint/no-explicit-any': 'off', // Allow any in test files for flexibility
      },
    },
    // Special rules for config files
    {
      files: ['vite.config.ts', 'jest.config.ts'],
      rules: {
        'import/no-default-export': 'off',
      },
    },
  ],
};