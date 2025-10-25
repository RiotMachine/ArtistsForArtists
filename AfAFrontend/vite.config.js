import { defineConfig } from 'vite'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = dirname(fileURLToPath(import.meta.url))

export default defineConfig({
    build: {
        rollupOptions: {
            input: resolve(__dirname, '/src/js/main.js'),
            output: {
                dir: resolve(__dirname, 'dist'),
                entryFileNames: 'bootstrap.js'
            },
        },
    },
    css: {
        preprocessorOptions: {
            scss: {
                // silence Bootstrap Sass deprecation warnings
                silenceDeprecations: [
                    'import',
                    'color-functions',
                    'global-builtin',
                ],
            },
        },
    },
})