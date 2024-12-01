# Gunicorn configuration file
timeout = 120  # Increase timeout to 120 seconds
workers = 2    # Number of worker processes
threads = 4    # Number of threads per worker
worker_class = 'gthread'  # Use threads
max_requests = 1000
max_requests_jitter = 50 