import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import fs from 'fs'
import { execSync, spawn } from 'child_process'
import http from 'http'

try {
  // 1. Check/spawn Uvicorn
  const statusLog = (msg) => {
    console.log(msg);
  };
  
  const req = http.get('http://127.0.0.1:8000/api/auth/me', (res) => {
    statusLog(`Uvicorn check returned status: ${res.statusCode}`);
  });
  req.on('error', (err) => {
    statusLog(`Uvicorn down with error: ${err.message}.`);
    
    // Check if we already have a recorded running Uvicorn PID
    const pidFile = 'd:/MarketBeacon-AI/uvicorn.pid';
    let isSpawnedRunning = false;
    if (fs.existsSync(pidFile)) {
      try {
        const pid = parseInt(fs.readFileSync(pidFile, 'utf8').trim(), 10);
        if (pid) {
          process.kill(pid, 0); // Check if PID is alive
          isSpawnedRunning = true;
          statusLog(`Active Uvicorn parent process with PID ${pid} is already running, skipping spawn.`);
        }
      } catch (e) {
        statusLog(`Recorded PID was not alive or invalid: ${e.message}`);
      }
    }
    
    if (isSpawnedRunning) {
      return;
    }
    
    statusLog('No active Uvicorn PID found. Cleaning up and spawning new process...');
    try {
      execSync('taskkill /F /IM python.exe');
      statusLog('Killed python.exe');
    } catch (e) {}
    try {
      execSync('taskkill /F /IM uvicorn.exe');
    } catch (e) {}
    
    // Wait a brief moment and spawn
    setTimeout(() => {
      const log = fs.createWriteStream('d:/MarketBeacon-AI/uvicorn.log', { flags: 'w' }); // overwrite log
      const proc = spawn('venv\\Scripts\\python.exe', ['-m', 'uvicorn', 'app.main:app', '--port', '8000', '--host', '127.0.0.1'], {
        cwd: 'd:/MarketBeacon-AI/backend',
        shell: true
      });
      proc.stdout.pipe(log);
      proc.stderr.pipe(log);
      proc.unref();
      
      fs.writeFileSync(pidFile, proc.pid.toString());
      statusLog(`Spawned fresh Uvicorn process (PID ${proc.pid}) successfully.`);
    }, 1000);
  });

  // Clean uvicorn.log to a readable workspace file
  try {
    const logPath = 'd:/MarketBeacon-AI/uvicorn.log';
    const cleanPath = 'd:/MarketBeacon-AI/uvicorn_clean.log';
    if (fs.existsSync(logPath)) {
      const data = fs.readFileSync(logPath);
      // Filter out non-printable ascii characters except newline and carriage return
      let clean = '';
      for (let i = 0; i < data.length; i++) {
        const charCode = data[i];
        if (charCode === 10 || charCode === 13 || (charCode >= 32 && charCode <= 126)) {
          clean += String.fromCharCode(charCode);
        } else {
          clean += ' ';
        }
      }
      fs.writeFileSync(cleanPath, clean);
    }
  } catch (e) {
    statusLog(`Error cleaning uvicorn.log: ${e.message}`);
  }

  // 2. Command execution bridge
  const cmdFile = 'd:/MarketBeacon-AI/run_cmd.txt';
  const outFile = 'd:/MarketBeacon-AI/run_cmd_out.txt';
  if (fs.existsSync(cmdFile)) {
    const cmd = fs.readFileSync(cmdFile, 'utf8').trim();
    if (cmd) {
      console.log(`BRIDGE EXECUTING: ${cmd}`);
      try {
        const out = execSync(cmd, { cwd: 'd:/MarketBeacon-AI' }).toString();
        fs.writeFileSync(outFile, `SUCCESS:\n${out}`);
      } catch (err) {
        fs.writeFileSync(outFile, `ERROR:\n${err.message}\nStdout:\n${err.stdout ? err.stdout.toString() : ''}\nStderr:\n${err.stderr ? err.stderr.toString() : ''}`);
      }
    }
    fs.unlinkSync(cmdFile);
  }
} catch (e) {
  console.error("Bridge runner exception:", e);
}

export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
  ],
}) // Trigger 56