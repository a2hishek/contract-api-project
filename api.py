from fastapi import FastAPI, File, UploadFile, HTTPException, Query
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from main import extract_from_pdf, perform_rag, llm_response, llm_response_stream, llm_audit
from rag import create_vector_store
from models import Extract, RAGData, AskRequest, Audit
import os
import logging
import re
from pathlib import Path
from typing import Optional
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Contract Intelligence API",
    description="API for extracting structured information from legal contracts",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
UPLOAD_DIR = Path("docs")
UPLOAD_DIR.mkdir(exist_ok=True)


def sanitize_filename(filename: str) -> str:
    """Sanitize filename to prevent path traversal attacks"""
    # Remove path components
    filename = os.path.basename(filename)
    # Remove special characters
    filename = re.sub(r'[^a-zA-Z0-9._-]', '_', filename)
    return filename

def get_filename(filename):
    # Determine which file to process
    if filename:
        # Sanitize filename
        safe_filename = sanitize_filename(filename)
        pdf_path = UPLOAD_DIR / safe_filename
        
        if not pdf_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"File '{safe_filename}' not found. Please upload the file first."
            )
    else:
        # Find the most recent PDF file
        pdf_files = list(UPLOAD_DIR.glob("*.pdf"))
        if not pdf_files:
            raise HTTPException(
                status_code=404,
                detail="No PDF files found. Please upload a file first using /ingest endpoint."
            )
        pdf_path = max(pdf_files, key=os.path.getctime)
        logger.info(f"Using most recent file: {pdf_path.name}")

    return pdf_path


@app.get("/")
def root():
    """Root endpoint"""
    return {
        "message": "Contract Intelligence API",
        "version": "1.0.0",
        "endpoints": {
            "upload": "/ingest",
            "extract": "/extract?filename=<filename>",
            "health": "/health"
        }
    }


@app.get("/about")
def about():
    """About endpoint"""
    return {
        "message": "Contract Intelligence API enables QnA with your legal contracts and performs structured data extraction",
        "features": [
            "PDF file upload",
            "Structured data extraction",
            "Contract information parsing"
        ]
    }


@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "Contract Intelligence API"}


@app.post("/ingest")
async def upload_pdf(file: UploadFile = File(...)):
    """
    Upload a PDF file for processing
    
    - **file**: PDF file to upload (max 10MB)
    """
    try:
        # Validate file type
        if file.content_type != "application/pdf":
            raise HTTPException(
                status_code=400,
                detail="Only PDF files are allowed. Please upload a valid PDF file."
            )
        
        # Read file content
        contents = await file.read()
        
        # Validate file size
        if len(contents) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"File size exceeds maximum allowed size of {MAX_FILE_SIZE / (1024*1024):.1f}MB"
            )
        
        # Validate PDF structure (basic check)
        if not contents.startswith(b'%PDF'):
            raise HTTPException(
                status_code=400,
                detail="Invalid PDF file. File does not appear to be a valid PDF."
            )
        
        # Sanitize filename
        safe_filename = sanitize_filename(file.filename) # type: ignore
        file_path = UPLOAD_DIR / safe_filename
        
        # Save file
        try:
            with open(file_path, "wb") as f:
                f.write(contents)

            file_path = str(file_path)
            if os.path.exists("docs/uploaded_files.json"):
                with open("docs/uploaded_files.json", "r") as f:
                    data = json.load(f)
                data["current_file"] = file_path
                if not data.get(file_path, ""):
                    create_vector_store(file_path)
                    data[file_path] = file_path
                    # data["current_file"] = file_path
                with open("docs/uploaded_files.json", "w") as f:
                    json.dump(data, f)

            else:
                create_vector_store(file_path)
                data = {str(file_path): file_path, "current_file": file_path}
                with open("docs/uploaded_files.json", "w") as f:
                    json.dump(data, f)
            
            

            logger.info(f"File uploaded successfully: {safe_filename}")
        except Exception as e:
            logger.error(f"Error saving file: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Error saving file: {str(e)}"
            )
        
        return JSONResponse(
            status_code=201,
            content={
                "message": "File uploaded successfully!",
                "filename": safe_filename,
                "size": len(contents),
                "path": file_path
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in upload_pdf: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@app.get("/extract", response_model=dict)
def extract_content(filename: Optional[str] = Query(None, description="Name of the PDF file to extract from")):
    """
    Extract structured data from a PDF file
    
    - **filename**: Optional filename. If not provided, uses the most recently uploaded file.
    """
    try:
        # Extract data from PDF
        pdf_path = get_filename(filename)

        try:
            result = extract_from_pdf(str(pdf_path))
            
            # Convert Pydantic model to dict
            if isinstance(result, Extract):
                data = result.model_dump()
            else:
                # If it's already a dict, use it directly
                data = result if isinstance(result, dict) else {"raw": str(result)}
            
            logger.info(f"Successfully extracted data from {pdf_path.name}")
            
            return {
                "status": "success",
                "filename": pdf_path.name,
                "data": data
            }
        
        except Exception as e:
            logger.error(f"Error extracting data: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Error extracting data from PDF: {str(e)}"
            )
    
    except Exception as e:
        logger.error(f"Unexpected error in extract_content: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )
    
@app.get("/rag")
def rag_retriveal(query: str):

    output, citations = perform_rag(query)

    return {"output": output, "citations": citations}

@app.post("/ask")
def llm_output(payload: AskRequest):
    """
    Generate final LLM answer using RAG context.
    """
    try:
        output = llm_response(query=payload.query, context=payload.rag_data.model_dump())
        return {"output": output}
    except Exception as e:
        logger.error(f"Error generating LLM output: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate response: {str(e)}")


@app.post("/ask/stream")
def llm_output_stream(payload: AskRequest):
    """
    Stream LLM answer using RAG context (Server-Sent Events).
    """

    def event_stream():
        try:
            for token in llm_response_stream(payload.query, payload.rag_data.model_dump()):
                if token:
                    yield f"data: {json.dumps({'token': token})}\n\n"
            # indicate completion
            yield "data: {\"event\": \"end\"}\n\n"
        except Exception as e:
            logger.error(f"Error generating streaming LLM output: {str(e)}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
    
@app.get("/audit", response_model=dict)
def audit_pdf(filename: Optional[str] = Query(None, description="Name of the PDF file to extract from")):


    pdf_path = get_filename(filename=filename)

    try:
        result = llm_audit(str(pdf_path))
        
        # Convert Pydantic model to dict
        if isinstance(result, Audit):
            data = result.model_dump()
        else:
            # If it's already a dict, use it directly
            data = result if isinstance(result, dict) else {"raw": str(result)}
        
        logger.info(f"Successfully auditted data from {pdf_path.name}")
        
        return {
            "status": "success",
            "filename": pdf_path.name,
            "data": data
        }
        
    except Exception as e:
        logger.error(f"Error auditing data: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error auditing data from PDF: {str(e)}"
        )

