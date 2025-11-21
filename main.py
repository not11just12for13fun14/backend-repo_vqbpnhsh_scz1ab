import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from typing import List
from schemas import QuoteRequest
from database import create_document

app = FastAPI(title="James Lee Builders API", description="Lead capture and content API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "James Lee Builders backend is running"}

@app.post("/api/quote")
def submit_quote(payload: QuoteRequest):
    try:
        # Persist to database (collection inferred from schema class name: quoterequest)
        doc_id = create_document("quoterequest", payload)
    except Exception as e:
        # Database might be unavailable; still continue to email step but return warning
        doc_id = None

    # Send email notification (simple SMTP via environment — optional)
    try:
        import smtplib
        from email.mime.text import MIMEText

        recipient = os.getenv("QUOTE_EMAIL_TO", "jamesleegrundy@gmail.com")
        sender = os.getenv("QUOTE_EMAIL_FROM", "no-reply@flames.blue")
        subject = "New Quote Request – James Lee Builders"
        body = (
            f"Name: {payload.name}\n"
            f"Email: {payload.email}\n"
            f"Phone: {payload.phone}\n"
            f"Project Type: {payload.projectType}\n"
            f"Postcode: {payload.postcode}\n\n"
            f"Message:\n{payload.message}\n\n"
            f"Record ID: {doc_id or 'not saved'}\n"
        )

        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = sender
        msg["To"] = recipient

        smtp_host = os.getenv("SMTP_HOST")
        smtp_port = int(os.getenv("SMTP_PORT", "587"))
        smtp_user = os.getenv("SMTP_USER")
        smtp_pass = os.getenv("SMTP_PASS")

        if smtp_host and smtp_user and smtp_pass:
            with smtplib.SMTP(smtp_host, smtp_port) as server:
                server.starttls()
                server.login(smtp_user, smtp_pass)
                server.sendmail(sender, [recipient], msg.as_string())
        # If SMTP not configured, we silently skip emailing.
    except Exception:
        pass

    return {"status": "ok", "id": doc_id}

@app.get("/api/portfolio")
def get_portfolio():
    # Static seed data for now – can be moved to DB later
    return [
        {
            "id": "proj-1",
            "title": "Driveway & Paving – Haslingden",
            "thumb": "/images/driveway1.jpg",
            "images": ["/images/driveway1.jpg", "/images/driveway1b.jpg"],
            "description": "Block-paved driveway with drainage and edging."
        },
        {
            "id": "proj-2",
            "title": "Brickwork & Garden Wall – Rawtenstall",
            "thumb": "/images/brickwork1.jpg",
            "images": ["/images/brickwork1.jpg", "/images/brickwork1b.jpg"],
            "description": "Reclaimed brick wall with coping stones."
        },
        {
            "id": "proj-3",
            "title": "Roofing Repair – Ramsbottom",
            "thumb": "/images/roof1.jpg",
            "images": ["/images/roof1.jpg", "/images/roof1b.jpg"],
            "description": "Slate tile replacement and flashing."
        },
    ]

@app.get("/test")
def test_database():
    """Test endpoint to check if database is available and accessible"""
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    
    try:
        # Try to import database module
        from database import db
        
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            
            # Try to list collections to verify connectivity
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]  # Show first 10 collections
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
            
    except ImportError:
        response["database"] = "❌ Database module not found (run enable-database first)"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"
    
    # Check environment variables
    import os
    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
    
    return response


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
