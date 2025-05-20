from fastapi import FastAPI, UploadFile, Form, BackgroundTasks
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from uuid import uuid4
from pathlib import Path
import shutil

# FastAPI app setup
app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Directory setup
DATA_DIR = Path("data")
RESULT_DIR = Path("result")
DATA_DIR.mkdir(exist_ok=True)
RESULT_DIR.mkdir(exist_ok=True)

@app.post("/trigger/")
def trigger_pipeline(files: list[UploadFile]):
    uuid = str(uuid4())
    print(f"Received files for UUID: {uuid}. files: {files}")
    if not files:
        return {"error": "No files provided."}
    if len(files) > 5:
        return {"error": "Too many files. Maximum is 5."}
    if not all(file.filename.endswith('.pdf') for file in files):
        return {"error": "All files must be PDFs."}

    uuid_dir = DATA_DIR / uuid
    uuid_dir.mkdir(parents=True, exist_ok=True)

    for file in files:
        file_path = uuid_dir / file.filename
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

    result_dir = RESULT_DIR / uuid
    result_dir.mkdir(parents=True, exist_ok=True)
    (result_dir / "eda.html").write_text("<html><body><h1>EDA Results</h1></body></html>")

    return {"status": "processing", "uuid": uuid}

@app.get("/EDA/{uuid}", response_class=HTMLResponse)
def get_eda_result(uuid: str):
    eda_file = RESULT_DIR / uuid / "eda.html"
    if eda_file.exists():
        return eda_file.read_text()
    return HTMLResponse("<html><body><h1>Pipeline still in progress. Check back later.</h1></body></html>", status_code=200)

@app.get("/chat/{uuid}")
def get_chat_status(uuid: str):
    metadata_file = RESULT_DIR / uuid / "metadata.pkl"
    index_file = RESULT_DIR / uuid / "index.faiss"

    if metadata_file.exists() and index_file.exists():
        return {"message": "Chatbot is ready. You can now interact with the semantic search."}

    return {"message": "Still processing. Try again later."}

class ChatRequest(BaseModel):
    message: str

@app.post("/chat/{uuid}")
def chat_with_backend(uuid: str, chat_request: ChatRequest):
    user_message = chat_request.message
    print(f"Received message: {user_message} for UUID: {uuid}")
    response_message = f"Processed your message: '{user_message}' for document {uuid}."
    return {"response": response_message}
