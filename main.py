from fastapi import FastAPI
from app.routes.dutch import router as dutch_router
from fastapi.middleware.cors import CORSMiddleware
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(dutch_router)

@app.get("/")
def root():
    return{"Hello"}