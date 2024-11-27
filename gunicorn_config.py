bind = '127.0.0.1:5000'
workers = 2
worker_class = 'sync'
worker_connections = 1000
timeout = 120
keepalive = 2

# 日志设置
accesslog = '/var/log/flask_app/gunicorn_access.log'
errorlog = '/var/log/flask_app/gunicorn_error.log'
loglevel = 'info'
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'
capture_output = True

# 进程名称
proc_name = 'flask_app'

# 优雅重启
graceful_timeout = 120
