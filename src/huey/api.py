from fastapi import FastAPI

app = FastAPI(title="HueyOS API", version="0.2.0")

@app.get("/healthz")
def healthz():
    return {"status": "ok", "service": "hueyos"}
