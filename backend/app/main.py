from fastapi import FastAPI

app = FastAPI(
    title="FooDiX API",
    version="0.1.0",
    description="Backend API for the FooDiX nutrition platform.",
)


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    return {"status": "ok", "service": "foodix-api"}
