from fastapi import FastAPI
from app.routes.dutch_routes import router as dutch_router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://dutch-front-end.vercel.app",
        # "http://localhost:4200",
        # "http://127.0.0.1:4200",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(dutch_router)


@app.get("/")
def root():
    return {"Hello"}
