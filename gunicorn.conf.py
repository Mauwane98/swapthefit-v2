import multiprocessing

workers = multiprocessing.cpu_count() * 2 + 1
worker_class = 'eventlet'
bind = '0.0.0.0:8000'
accesslog = 'logs/app.log'
errorlog = 'logs/app.log'
