import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// NOTE: This config previously contained a "bridge" that read a command from a
// file in the repository root, executed it with a shell, and force-killed all
// local Python processes. That made `npm run dev` run arbitrary repo-controlled
// commands on a developer machine. It has been removed and must not come back.
//
// Run the backend and frontend as two separate processes -- see README.md.

export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
  ],
})
