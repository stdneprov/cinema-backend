import falcon.asgi
from minio import Minio
from minio.error import S3Error
import os
from settings import MINIO_ENDPOINT, MINIO_ACCESS_KEY, MINIO_SECRET_KEY

class StreamingResource:
    def __init__(self):
        self.client = Minio(
            MINIO_ENDPOINT,
            access_key=MINIO_ACCESS_KEY,
            secret_key=MINIO_SECRET_KEY,
            secure=False
        )

    async def on_get(self, req, resp, uuid):
        bucket_name = "movies"
        try:
            # Получаем объект из S3
            stat = self.client.stat_object(bucket_name, uuid)
            file_size = stat.size

            # Проверяем заголовок Range
            range_header = req.get_header('Range')
            start = 0
            end = file_size - 1

            if range_header:
                # Парсим диапазон
                range_header = range_header.replace('bytes=', '')
                parts = range_header.split('-')
                start = int(parts[0]) if parts[0] else 0
                end = int(parts[1]) if len(parts) > 1 and parts[1] else file_size - 1

                if end >= file_size:
                    end = file_size - 1

            length = end - start + 1

            # Устанавливаем заголовки ответа
            resp.status = falcon.HTTP_206 if range_header else falcon.HTTP_200
            resp.content_type = 'video/mp4'
            resp.append_header('Content-Range', f'bytes {start}-{end}/{file_size}')
            resp.append_header('Accept-Ranges', 'bytes')
            resp.append_header('Content-Length', str(length))

            # Читаем и отправляем данные по частям
            response = self.client.get_object(bucket_name, uuid, offset=start, length=length)
            resp.stream = response.stream(64 * 1024)  # Стриминг по 64KB для лучшей производительности
        
        except S3Error as e:
            resp.status = falcon.HTTP_404
            resp.text = f"File not found: {str(e)}"
        except Exception as e:
            resp.status = falcon.HTTP_500
            resp.text = f"Internal server error: {str(e)}"
