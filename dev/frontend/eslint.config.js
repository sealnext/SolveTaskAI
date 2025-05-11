import js from '@eslint/js';
import globals from 'globals';
import tseslint from 'typescript-eslint';
import pluginReact from 'eslint-plugin-react';
import { defineConfig } from 'eslint/config';
import reactHooks from 'eslint-plugin-react-hooks';
import importX from 'eslint-plugin-import-x';
import nodePlugin from 'eslint-plugin-n';
import tanstackQuery from '@tanstack/eslint-plugin-query';

export default defineConfig([
	{ files: ['**/*.{js,mjs,cjs,ts,jsx,tsx}'], plugins: { js }, extends: ['js/recommended'] },
	{ files: ['**/*.{js,mjs,cjs,ts,jsx,tsx}'], languageOptions: { globals: globals.browser } },
	{
		files: ['**/*.{js,ts,jsx,tsx}'],
		plugins: { 'import-x': importX },
		rules: { 'import-x/order': 'error' },
	},
	{
		files: ['**/*.{js,mjs,cjs}'],
		plugins: { n: nodePlugin },
		rules: {
			...nodePlugin.configs.recommended.rules,
			'n/no-unpublished-import': 'off'
		}
	},
	{
		files: ['**/*.{ts,tsx}'],
		plugins: { '@tanstack/query': tanstackQuery },
		rules: tanstackQuery.configs.recommended.rules
	},
	tseslint.configs.recommended,
	pluginReact.configs.flat.recommended,
	reactHooks.configs['recommended-latest'],
]);
