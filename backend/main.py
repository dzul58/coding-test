from fastapi import FastAPI, Request, Query, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any, Optional
import uvicorn
import json
from pydantic import BaseModel
import google.generativeai as genai
import os
from dotenv import load_dotenv
import logging
from urllib.parse import unquote
from math import ceil
from pathlib import Path

# Load environment variables from backend/.env
env_path = Path(__file__).resolve().parent / '.env'
load_dotenv(dotenv_path=env_path)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Sales Dashboard API",
    description="API for serving sales data and AI-powered insights",
    version="1.0.0"
)

# Add CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update with specific origins in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure Gemini AI
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    logger.error("GEMINI_API_KEY not found in environment variables")
    raise ValueError("GEMINI_API_KEY not found in environment variables. Please check your backend/.env file.")

try:
    genai.configure(api_key=GEMINI_API_KEY)
    logger.info("Successfully configured Gemini AI with API key")
except Exception as e:
    logger.error(f"Failed to configure Gemini AI: {str(e)}")
    raise ValueError(f"Failed to configure Gemini AI: {str(e)}")

# Load dummy data
def load_data():
    try:
        with open("../dummyData.json", "r") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading data: {e}")
        raise HTTPException(status_code=500, detail="Error loading data")

# Pydantic model for AI request - making data field optional
class AIRequest(BaseModel):
    question: str
    data: Optional[Dict[str, Any]] = None

# Common pagination parameters
def get_pagination_params(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Number of items per page")
):
    return {"page": page, "page_size": page_size}

# Helper function to filter data based on search query
def search_data(data: List[Dict], query: str) -> List[Dict]:
    if not query:
        return data
    
    query = query.lower()
    results = []
    
    # Use a set to track IDs of items already added to results
    added_ids = set()
    
    for item in data:
        # Skip if this item is already in results
        if item.get("id") in added_ids:
            continue
            
        # Search in name, role, region - these are the primary search fields
        if (query in item.get("name", "").lower() or
            query in item.get("role", "").lower() or
            query in item.get("region", "").lower()):
            results.append(item)
            added_ids.add(item.get("id"))
            continue
        
        # Search in skills (specifically prioritized)
        if any(query in skill.lower() for skill in item.get("skills", [])):
            results.append(item)
            added_ids.add(item.get("id"))
            continue
    
    return results

# Apply pagination to data
def paginate_data(data: List, page: int, page_size: int) -> Dict:
    total_items = len(data)
    total_pages = ceil(total_items / page_size)
    
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    
    paginated_data = data[start_idx:end_idx]
    
    return {
        "data": paginated_data,
        "meta": {
            "page": page,
            "page_size": page_size,
            "total_items": total_items,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1
        }
    }

@app.get("/api/sales-reps", tags=["Data"])
def get_data(
    name: Optional[str] = Query(None, description="Search by representative name"),
    role: Optional[str] = Query(None, description="Search by role"),
    region: Optional[str] = Query(None, description="Search by region"),
    skills: Optional[str] = Query(None, description="Search by skills"),
    pagination: Dict = Depends(get_pagination_params)
):
    """
    Returns sales representatives data with search filtering and pagination.
    
    - **name**: Optional search term to filter by representative name
    - **role**: Optional search term to filter by role
    - **region**: Optional search term to filter by region
    - **skills**: Optional search term to filter by skills
    - **page**: Page number for pagination (starts at 1)
    - **page_size**: Number of items per page
    """
    try:
        # Load data
        data = load_data()
        
        # Get sales reps data
        sales_reps = data.get("salesReps", [])
        
        # Apply search filters if provided
        if name or role or region or skills:
            filtered_reps = []
            for rep in sales_reps:
                # Check each search criterion
                name_match = True if not name else name.lower() in rep.get("name", "").lower()
                role_match = True if not role else role.lower() in rep.get("role", "").lower()
                region_match = True if not region else region.lower() in rep.get("region", "").lower()
                
                # Skills match
                skills_match = True
                if skills:
                    skills_match = False
                    for skill in rep.get("skills", []):
                        if skills.lower() in skill.lower():
                            skills_match = True
                            break
                
                # Only include if all provided criteria match
                if name_match and role_match and region_match and skills_match:
                    filtered_reps.append(rep)
            
            sales_reps = filtered_reps
            
        # Apply pagination
        result = paginate_data(
            sales_reps, 
            pagination["page"], 
            pagination["page_size"]
        )
        
        return result
    except Exception as e:
        logger.error(f"Error processing request: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/ai", tags=["AI"])
async def ai_endpoint(request: AIRequest):
    """
    Accepts a user question and optionally sales data, returns an AI-generated response using Google's Gemini model.
    If no data is provided, automatically loads data from dummyData.json.
    
    - **question**: The user's question about sales data
    - **data**: (Optional) The sales data to analyze - if not provided, will use dummyData.json
    """
    try:
        # Use data from request if provided, otherwise load from file
        if request.data is None:
            logger.info("No data provided in request, loading from file")
            data = load_data()
        else:
            data = request.data
        
        # Get sales reps data
        sales_reps = data.get("salesReps", [])
        
        if not sales_reps:
            logger.warning("No sales representatives data found")
            return {"answer": "Sales data is empty or not in the expected format."}
        
        # Extract sample data for richer context
        sample_rep = sales_reps[0] if sales_reps else {}
        
        # Create a summarized context from the data
        total_reps = len(sales_reps)
        regions = list(set(rep.get("region", "") for rep in sales_reps if rep.get("region")))
        roles = list(set(rep.get("role", "") for rep in sales_reps if rep.get("role")))
        
        # Process the data to remove quotes from status values
        for rep in sales_reps:
            for deal in rep.get("deals", []):
                if "status" in deal:
                    # Remove quotes from status values
                    deal["status"] = deal["status"].replace('"', '')
        
        # Prepare a system prompt with context that explicitly instructs not to use escaped quotes
        context = f"""
        You are a sales analysis assistant. The data contains information about {total_reps} sales representatives 
        across various regions including {', '.join(regions)}. 
        Their roles include {', '.join(roles)}.
        
        IMPORTANT: Do not use quotes when referring to status values like Closed Won, In Progress, or Closed Lost.
        Simply write the status directly without any quotation marks.
        
        Each sales representative has the following data structure:
        - id: unique identifier
        - name: representative's name
        - role: position
        - region: geographical area
        - skills: list of professional skills
        - deals: list of deals (client, value, status)
        - clients: list of clients (name, industry, contact)
        
        Complete data: {json.dumps(data, indent=2)}
        
        Answer the question based on this context specifically and helpfully. Provide the answer in English.
        Do NOT use quotation marks around status values in your response.
        """
        
        # Choose available model
        model_name = "gemini-1.5-flash"  # Fast model
        try:
            model = genai.GenerativeModel(model_name)
            logger.info(f"Using {model_name} model")
        except Exception as model_error:
            logger.error(f"Model {model_name} not available: {model_error}")
            # If model not available, try alternative model
            model_name = "gemini-1.5-pro"
            try:
                model = genai.GenerativeModel(model_name)
                logger.info(f"Fallback to {model_name} model")
            except Exception as fallback_error:
                logger.error(f"Fallback model also failed: {fallback_error}")
                return {"answer": "Sorry, AI service is currently unavailable. Please try again later."}
        
        # Start chat session
        chat = model.start_chat(history=[])
        
        # Send message to model
        response = chat.send_message(
            f"{context}\n\nQuestion: {request.question}"
        )
        
        # Clean up the response to remove escaped quotes and newlines
        clean_response = response.text.replace('\\n', ' ').replace('\\"', '"').replace('"Closed Won"', 'Closed Won').replace('"In Progress"', 'In Progress').replace('"Closed Lost"', 'Closed Lost').strip()
        
        return {"answer": clean_response}
    except Exception as e:
        logger.error(f"Error processing AI request: {e}")
        # Kembalikan HTTP Exception 500 untuk error yang tidak tertangani
        raise HTTPException(status_code=500, detail=f"AI processing error: {str(e)}")

if __name__ == "__main__":
    logger.info("Starting Sales Dashboard API...")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)