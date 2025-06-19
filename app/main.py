from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from app.api.routes import user
from app.db.init_db import init_db


app = FastAPI()

@app.on_event("startup")
def startup_event():
    init_db()

app.include_router(user.router)

app.mount("/static", StaticFiles(directory="app/static"), name="static")

templates = Jinja2Templates(directory="app/templates")


@app.get("/", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@app.post("/login", response_class=HTMLResponse)
def handle_login(request: Request, email: str = Form(...), password: str = Form(...)):
    if email == "avocat@legalhub.fr" and password == "1234":
        user = {"nom": "Dupont"}
        return templates.TemplateResponse("dashboard_avocat.html", {"request": request, "user": user})
    else:
        return templates.TemplateResponse("login.html", {"request": request, "error": "Identifiants incorrects"})
