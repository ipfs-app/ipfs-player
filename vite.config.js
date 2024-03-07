import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [vue()],
  server: {
    proxy: {
      '/ipfs': {
        target: 'http://127.0.0.1:8080',
        secure: false,
        changeOrigin: true,
      }
    }
  },
  build:{
    assetsDir: "./",
    rollupOptions:{
      output:{
        entryFileNames:"[hash].js",
        assetFileNames: "[hash].[ext]"
      }
    }
  },
  base: "./"
})
