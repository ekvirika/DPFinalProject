import webbrowser

import uvicorn

from infra.api.app import app

if __name__ == "__main__":
    # Run the FastAPI application using Uvicorn
    webbrowser.open("http://127.0.0.1:8000/docs")
    uvicorn.run(app, host="127.0.0.1", port=8000)
