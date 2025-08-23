"""
Quick Database Viewer - Simple UI to browse VectorBid database
"""
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import text
from app.db.database import get_sync_session
from sqlalchemy.orm import Session

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/db", response_class=HTMLResponse)
async def database_viewer(request: Request, db: Session = Depends(get_sync_session)):
    """Simple database browser UI"""
    
    # Get list of tables
    tables_result = db.execute(text("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        ORDER BY table_name
    """))
    tables = [row[0] for row in tables_result]
    
    # Get basic counts for each table
    table_counts = {}
    for table in tables:
        try:
            count_result = db.execute(text(f"SELECT COUNT(*) FROM {table}"))
            table_counts[table] = count_result.scalar()
        except:
            table_counts[table] = "Error"
    
    return templates.TemplateResponse("db_viewer.html", {
        "request": request,
        "tables": tables,
        "table_counts": table_counts
    })

@router.get("/db/{table_name}", response_class=HTMLResponse)
async def view_table(request: Request, table_name: str, db: Session = Depends(get_sync_session)):
    """View specific table data"""
    
    try:
        # Get table columns
        columns_result = db.execute(text(f"""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = '{table_name}' AND table_schema = 'public'
            ORDER BY ordinal_position
        """))
        columns = [(row[0], row[1]) for row in columns_result]
        
        # Get table data (limit to 50 rows)
        data_result = db.execute(text(f"SELECT * FROM {table_name} LIMIT 50"))
        rows = data_result.fetchall()
        
        return templates.TemplateResponse("table_viewer.html", {
            "request": request,
            "table_name": table_name,
            "columns": columns,
            "rows": rows
        })
        
    except Exception as e:
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": f"Error viewing table {table_name}: {str(e)}"
        })