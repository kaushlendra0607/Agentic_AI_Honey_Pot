from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.api.routes import router as honeypot_router

# 1. Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("uvicorn.error")

app = FastAPI(title="Agentic Honeypot")

# 2. Add CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. THE DEBUGGER
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    error_details = exc.errors()
    logger.error(f"❌ VALIDATION ERROR: {error_details}")
    
    try:
        body = await request.json()
        logger.error(f"📩 RECEIVED BODY: {body}")
    except:
        logger.error("Could not read body")

    return JSONResponse(
        status_code=422,
        content={"detail": error_details, "body": "Check logs for details"},
    )

# 4. Include Router
# ✅ FIX: Use the imported router object directly
app.include_router(honeypot_router)

# --- ✅ NEW: HEALTH CHECKS TO FIX "ACCESS_ERROR" ---
@app.get("/")
async def root():
    """
    Root endpoint for availability checks.
    Fixes the 404 error when the tester pings the base URL.
    """
    return {"status": "active", "message": "Honeypot is running"}

@app.get("/health")
async def health_check():
    """
    Standard health check endpoint.
    """
    return {"status": "ok"}
# ---------------------------------------------------

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)