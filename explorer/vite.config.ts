import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig(({ command }) => ({
  plugins: [react()],
  // Local dev: http://localhost:5173/ ; Pages: https://softlang.github.io/langde/
  base: command === 'build' ? '/langde/' : '/',
}));
