from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.responses import JSONResponse
from starlette.status import HTTP_403_FORBIDDEN, HTTP_401_UNAUTHORIZED, HTTP_404_NOT_FOUND
from starlette.exceptions import HTTPException as StarletteHTTPException


from app.db.init_db import init_db
from app.api.routes import auth, admin, avocat, clarck,dossier


app = FastAPI()

@app.on_event("startup")
def startup_event():
    init_db()

app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(avocat.router)
app.include_router(clarck.router)
app.include_router(dossier.router)


app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

@app.exception_handler(StarletteHTTPException)
async def custom_http_exception_handler(request: Request, exc: StarletteHTTPException):
    if exc.status_code == HTTP_401_UNAUTHORIZED:
        return templates.TemplateResponse("error/401.html", {
            "request": request,
            "detail": exc.detail
        }, status_code=401)
    elif exc.status_code == HTTP_403_FORBIDDEN:
        return templates.TemplateResponse("error/403.html", {
            "request": request,
            "detail": exc.detail
        }, status_code=403)
    elif exc.status_code == HTTP_404_NOT_FOUND:
        return templates.TemplateResponse("error/404.html", {
            "request": request,
            "detail": exc.detail
        }, status_code=404)

    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})