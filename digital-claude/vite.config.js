import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  base: '/reports/blueprint-flow-assets/',
  build: {
    outDir: 'reports/blueprint-flow-assets',
    emptyOutDir: true,
    rollupOptions: {
      input: 'frontend/blueprint-flow/src/main.jsx',
      output: {
        entryFileNames: 'blueprint-flow.js',
        chunkFileNames: 'chunks/[name]-[hash].js',
        assetFileNames: 'blueprint-flow.[ext]',
      },
    },
  },
});
