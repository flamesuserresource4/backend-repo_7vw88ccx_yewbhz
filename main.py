from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

from database import db, create_document, get_documents
from schemas import Wish as WishSchema

class WishOut(BaseModel):
    id: str
    name: str
    message: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

app = FastAPI(title="Birthday Game Interact API")

# CORS to allow frontend to call API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"status": "ok", "message": "Birthday API running"}


@app.get("/test")
def test():
    try:
        if db is None:
            return {
                "backend": "fastapi",
                "database": "mongodb",
                "connection_status": "unavailable",
                "error": "DATABASE_URL or DATABASE_NAME not configured"
            }
        collections = db.list_collection_names()
        return {
            "backend": "fastapi",
            "database": "mongodb",
            "database_url": "configured",
            "database_name": db.name,
            "connection_status": "ok",
            "collections": collections,
        }
    except Exception as e:
        return {
            "backend": "fastapi",
            "database": "mongodb",
            "connection_status": "error",
            "error": str(e)
        }


@app.get("/wishes", response_model=List[WishOut])
def get_wishes(limit: int = 50):
    """Return latest wishes (newest first)"""
    if db is None:
        raise HTTPException(status_code=500, detail="Database not available")
    cursor = db["wish"].find({}).sort("created_at", -1).limit(limit)
    results: List[WishOut] = []
    for doc in cursor:
        results.append(
            WishOut(
                id=str(doc.get("_id")),
                name=doc.get("name", ""),
                message=doc.get("message", ""),
                created_at=doc.get("created_at"),
                updated_at=doc.get("updated_at"),
            )
        )
    return results


@app.post("/wishes", response_model=WishOut)
def create_wish(payload: WishSchema):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not available")

    name = payload.name.strip()
    message = payload.message.strip()
    if not name or not message:
        raise HTTPException(status_code=400, detail="Name and message are required")

    inserted_id = create_document("wish", payload)
    doc = db["wish"].find_one({"_id": db["wish"].inserted_id}) if False else db["wish"].find_one({"_id": __import__('bson').ObjectId(inserted_id)})
    # Build response
    return WishOut(
        id=inserted_id,
        name=doc.get("name", name),
        message=doc.get("message", message),
        created_at=doc.get("created_at"),
        updated_at=doc.get("updated_at"),
    )
