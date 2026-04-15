from fastapi import FastAPI

app = FastAPI(title="Hello World API")


@app.get("/")
def root():
    return {"message": "Hello, subramanyam!!!123123123!!"}


@app.get("/health")
def health():
    return {"status": "ok"}
