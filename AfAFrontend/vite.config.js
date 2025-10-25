import { defineConfig } from 'vite'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
// docs say to have this next import; still trying to get it to work
// import 'vite/modulepreload-polyfill'

const __dirname = dirname(fileURLToPath(import.meta.url))

export default defineConfig({
    build: {
        cssCodeSplit: false,
        rollupOptions: {
            input: resolve(__dirname, '/src/js/main.js'),
            output: {
                dir: resolve(__dirname, 'dist'),
                entryFileNames: 'bootstrap.js'
            },
        },
    },
})