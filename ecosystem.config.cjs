// PM2 ecosystem configuration for Registry Review API.
//
// Why this exists: On Jan 14, 2026, the process crashed and PM2 tried to
// restart it, but the old socket hadn't released port 8003. Each restart
// failed with EADDRINUSE within ~6.5 seconds. With no backoff, PM2 cycled
// through 8,703 failed restarts over 16 hours before the port freed up.
//
// The three key settings that prevent this:
//   kill_timeout    — gives uvicorn time to release the socket on shutdown
//   listen_timeout  — waits for the app to actually start listening before
//                     declaring it "online"
//   exp_backoff_restart_delay — doubles the retry delay on each failure,
//                               capping at ~15 minutes instead of hammering
//                               every 5 seconds forever
//
// Usage:
//   pm2 start ecosystem.config.cjs        # first time (replaces ad-hoc start)
//   pm2 restart registry-review-api       # subsequent restarts
//   pm2 delete registry-review-api && pm2 start ecosystem.config.cjs  # reload config

module.exports = {
  apps: [
    {
      name: "registry-review-api",
      script: "chatgpt_rest_api.py",
      interpreter: ".venv/bin/python",
      cwd: "/opt/projects/registry-eliza/regen-registry-review-mcp",

      // Shutdown: give uvicorn 10s to finish requests and release the socket.
      // Default is 1600ms, which races with TCP TIME_WAIT.
      kill_timeout: 10000,

      // Startup: wait up to 15s for the app to bind the port.
      // Without this, PM2 considers the process "online" instantly,
      // even if uvicorn hasn't bound yet.
      listen_timeout: 15000,

      // Restart backoff: on repeated failures, double the delay each time
      // (100ms → 200ms → 400ms → ... capping at ~15min).
      // This turns a 16-hour restart storm into a few quiet retries.
      exp_backoff_restart_delay: 100,

      // Memory ceiling: restart if RSS exceeds 1GB.
      // Current baseline is ~340MB. This catches runaway growth.
      max_memory_restart: "1G",

      // Logging
      error_file: "logs/pm2-error.log",
      out_file: "logs/pm2-out.log",
      merge_logs: true,
      log_date_format: "YYYY-MM-DD HH:mm:ss",
    },
  ],
};
