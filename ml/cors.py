import falcon
import logging

class CORSMiddleware:
    def __init__(self):
        self.allowed_origins = ['*']  # Или задайте список разрешённых источников
    
    async def process_request(self, req, resp):
        logging.info(f"Processing request: {req.method} {req.url}")
        resp.set_header('Access-Control-Allow-Origin', '*')
        resp.set_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        resp.set_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        resp.set_header('Access-Control-Allow-Credentials', 'true')

        if req.method == 'OPTIONS':
            resp.status = falcon.HTTP_200
            return

    # Исправленная версия process_response с 5 аргументами
    async def process_response(self, req, resp, resource, req_succeeded):
        logging.info(f"Response: {resp.status}")
        # Можно добавить дополнительную логику здесь, если нужно
