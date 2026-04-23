import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    // Allow access from Tailscale funnel / shared tailnet hosts.
    // Wildcard leading dot matches any *.ts.net subdomain.
    allowedHosts: ['.ts.net'],
    proxy: {
      '/api': 'http://localhost:8001',
      '/health': 'http://localhost:8001',
    },
  },
})
