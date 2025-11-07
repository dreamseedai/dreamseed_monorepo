const js = require('@eslint/js');
const tseslint = require('typescript-eslint');

module.exports = tseslint.config(
  js.configs.recommended,
  ...tseslint.configs.recommended,
  {
    languageOptions: {
      parserOptions: {
        project: './tsconfig.json',
      },
    },
    rules: {
      'prettier/prettier': 'error',
    },
    settings: {
      'import/resolver': {
        alias: {
          map: [
            ['@', './src'],
            ['shared-analytics-ui', '../shared-analytics-ui/src'],
          ],
          extensions: ['.ts', '.tsx', '.js', '.jsx'],
        },
      },
    },
  }
);
