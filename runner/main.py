import uvicorn
from fastapi import FastAPI

from infra.api.app import app

if __name__ == "__main__":
    # Run the FastAPI application using Uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)