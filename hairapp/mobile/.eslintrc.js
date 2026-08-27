module.exports = {
  root: true,
  parser: '@typescript-eslint/parser',
  parserOptions: { ecmaFeatures: { jsx: true }, ecmaVersion: 2022, sourceType: 'module' },
  plugins: ['@typescript-eslint'],
  extends: ['eslint:recommended', 'plugin:@typescript-eslint/recommended'],
  env: { es2022: true, node: true },
  globals: { __DEV__: 'readonly', FormData: 'readonly', fetch: 'readonly', Response: 'readonly', BodyInit: 'readonly', AbortSignal: 'readonly', URL: 'readonly', describe: 'readonly', it: 'readonly', expect: 'readonly' },
  ignorePatterns: ['node_modules/', 'babel.config.js', '.eslintrc.js', 'jest.config.js'],
  rules: {
    '@typescript-eslint/no-unused-vars': ['error', { argsIgnorePattern: '^_' }],
    '@typescript-eslint/no-explicit-any': 'error',
    // El backend no manda texto de interfaz: si aparece un string literal
    // largo en JSX es que alguien se saltó el catálogo i18n.
    'no-restricted-syntax': [
      'error',
      {
        selector: 'JSXText[value=/[A-Za-zÁÉÍÓÚáéíóúÑñ]{4,}/]',
        message: 'Todo el texto visible sale del catálogo i18n. Usa t() o tKey().',
      },
    ],
  },
};
