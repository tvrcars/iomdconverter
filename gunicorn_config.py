# Gunicorn configuration file
timeout = 300  # Increase timeout to 5 minutes
workers = 1    # Reduce to 1 worker to conserve memory
threads = 2    # Reduce threads
worker_class = 'gthread'
max_requests = 1000
max_requests_jitter = 50
worker_tmp_dir = '/dev/shm'  # Use RAM for temporary files
worker_max_requests = 50     # Restart workers periodically
worker_max_requests_jitter = 10
limit_request_line = 0       # Unlimited request line size
limit_request_fields = 32768