from fastapi import FastAPI

app = FastAPI(title="Hello World API")


@app.get("/")
def root():
    return {"message": "Hello, Subu!"}


@app.get("/health")
def health():
    return {"status": "ok"}
