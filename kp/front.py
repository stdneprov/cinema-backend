from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

# Создаем объект Jinja2Templates
templates = Jinja2Templates(directory="front")

# Создаем роутер
router = APIRouter()

# Главная страница, которая будет рендерить HTML-шаблон
@router.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    # Здесь передаем данные для шаблона
    return templates.TemplateResponse("user-dashboard.html", {"request": request})

@router.get("/adminUpload", response_class=HTMLResponse)
async def read_root(request: Request):
    # Здесь передаем данные для шаблона
    return templates.TemplateResponse("admin-upload.html", {"request": request})

# Другой маршрут для рендеринга страницы
@router.get("/login", response_class=HTMLResponse)
async def about_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

