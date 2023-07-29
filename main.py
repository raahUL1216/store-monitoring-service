import uvicorn
import os

if __name__ == "__main__":
  env = os.getenv('ENVIRONMENT', 'dev')

  if env == 'dev':
    host = '127.0.0.1'
  else:
    host = '0.0.0.0'

  uvicorn.run("server.api:app", host=host, port=8000, reload=True)
