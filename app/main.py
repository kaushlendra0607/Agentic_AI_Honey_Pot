import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# 1. Load Environment Variables (Best to do this first)
load_dotenv()

from app.api.routes import router

# 2. Initialize App
app = FastAPI(title="Agentic Honeypot API", version="1.0.0")

# 3. Add CORS Middleware (CRITICAL for Frontend Integration)
# allow_origins=["*"] allows ANY website to talk to your bot.
# This is unsafe for real banks, but PERFECT for hackathons to avoid errors.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 4. Include Routes
app.include_router(router)

@app.get("/health")
def health():
    return {"status": "ok", "env": "loaded"}

if __name__ == "__main__":
    import uvicorn
    # This allows you to run "python app/main.py" directly
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)