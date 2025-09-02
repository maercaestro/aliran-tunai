module.exports = {
  apps: [{
    name: 'aliran-api',
    script: 'api_server.py',
    interpreter: 'python3',
    cwd: '/Users/abuhuzaifahbidin/Documents/GitHub/aliran-tunai',
    env: {
      NODE_ENV: 'production'
    },
    instances: 1,
    autorestart: true,
    watch: false,
    max_memory_restart: '1G',
    error_file: './logs/api-error.log',
    out_file: './logs/api-out.log',
    log_file: './logs/api-combined.log',
    time: true
  }]
};
