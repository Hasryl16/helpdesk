from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.config import settings
from app.routers import auth, tickets, users

app = FastAPI(title="HelpDesk Mini API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(StarletteHTTPException)
async def http_error(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    return JSONResponse({"error": {"status": exc.status_code, "message": exc.detail}}, status_code=exc.status_code)


@app.exception_handler(RequestValidationError)
async def validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
    body = {"error": {"status": 422, "message": "Validation error", "details": jsonable_encoder(exc.errors())}}
    return JSONResponse(body, status_code=422)


app.include_router(auth.router)
app.include_router(users.router)
app.include_router(tickets.router)
