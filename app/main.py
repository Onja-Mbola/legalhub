import os

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.responses import JSONResponse
from starlette.status import HTTP_403_FORBIDDEN, HTTP_401_UNAUTHORIZED, HTTP_404_NOT_FOUND, HTTP_400_BAD_REQUEST, \
    HTTP_500_INTERNAL_SERVER_ERROR
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.db.init_db import init_db
from app.api.routes import clarck
from app.api.routes.avocat import dossier, avocat, enrolement, requete_assignation, premiere_audience, \
    echange_conclusion, deliberation_decision, decision_definitive, decision_avant_dire_droit, jugement, opposition, \
    retour_audience, jugement_definitif
from app.api.routes.admin import admin, auth, param_general

app = FastAPI()


@app.on_event("startup")
def startup_event():
    init_db()


app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(param_general.router)
app.include_router(avocat.router)
app.include_router(clarck.router)
app.include_router(dossier.router)
app.include_router(enrolement.router)
app.include_router(requete_assignation.router)
app.include_router(premiere_audience.router)
app.include_router(echange_conclusion.router)
app.include_router(deliberation_decision.router)
app.include_router(decision_avant_dire_droit.router)
app.include_router(decision_definitive.router)
app.include_router(jugement.router)
app.include_router(opposition.router)
app.include_router(retour_audience.router)
app.include_router(jugement_definitif.router)

documents_path = "app/documents"
if not os.path.exists(documents_path):
    os.makedirs(documents_path)

app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.mount("/documents", StaticFiles(directory="app/documents"), name="documents")
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
    elif exc.status_code == HTTP_400_BAD_REQUEST:
        return templates.TemplateResponse("error/400.html", {
            "request": request,
            "detail": exc.detail
        }, status_code=400)
    elif exc.status_code == HTTP_500_INTERNAL_SERVER_ERROR:
        return templates.TemplateResponse("error/500.html", {
            "request": request,
            "detail": exc.detail
        }, status_code=500)

    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
