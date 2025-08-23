"""
Quick Database Viewer - Simple UI to browse VectorBid database
"""
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import text
from app.db.database import get_sync_session
from sqlalchemy.orm import Session
import json

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

@router.get("/db/schema", response_class=HTMLResponse)
async def database_schema(request: Request, db: Session = Depends(get_sync_session)):
    """Visual database schema with relationships"""
    
    # Get all tables
    tables_result = db.execute(text("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        ORDER BY table_name
    """))
    tables = [row[0] for row in tables_result]
    
    # Get foreign key relationships
    relationships = []
    for table in tables:
        fk_result = db.execute(text(f"""
            SELECT 
                tc.constraint_name,
                tc.table_name,
                kcu.column_name,
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name,
                rc.match_option,
                rc.update_rule,
                rc.delete_rule
            FROM information_schema.table_constraints AS tc 
            JOIN information_schema.key_column_usage AS kcu
                ON tc.constraint_name = kcu.constraint_name
                AND tc.table_schema = kcu.table_schema
            JOIN information_schema.constraint_column_usage AS ccu
                ON ccu.constraint_name = tc.constraint_name
                AND ccu.table_schema = tc.table_schema
            JOIN information_schema.referential_constraints AS rc
                ON tc.constraint_name = rc.constraint_name
                AND tc.table_schema = rc.constraint_schema
            WHERE tc.constraint_type = 'FOREIGN KEY' 
                AND tc.table_name = '{table}'
                AND tc.table_schema = 'public'
        """))
        
        for row in fk_result:
            relationships.append({
                'from_table': row[1],
                'from_column': row[2],
                'to_table': row[3],
                'to_column': row[4],
                'constraint_name': row[0],
                'update_rule': row[6],
                'delete_rule': row[7],
                'relationship_type': 'lookup'  # Could be enhanced to detect master-detail
            })
    
    return templates.TemplateResponse("schema_viewer.html", {
        "request": request,
        "tables": json.dumps(tables),
        "relationships": json.dumps(relationships)
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

@router.get("/db/{table_name}/relationships", response_class=HTMLResponse)
async def table_relationships(request: Request, table_name: str, db: Session = Depends(get_sync_session)):
    """View specific table relationships"""
    
    # Get outgoing relationships (this table references others)
    outgoing_result = db.execute(text(f"""
        SELECT 
            tc.constraint_name,
            kcu.column_name,
            ccu.table_name AS foreign_table_name,
            ccu.column_name AS foreign_column_name,
            rc.update_rule,
            rc.delete_rule
        FROM information_schema.table_constraints AS tc 
        JOIN information_schema.key_column_usage AS kcu
            ON tc.constraint_name = kcu.constraint_name
        JOIN information_schema.constraint_column_usage AS ccu
            ON ccu.constraint_name = tc.constraint_name
        JOIN information_schema.referential_constraints AS rc
            ON tc.constraint_name = rc.constraint_name
        WHERE tc.constraint_type = 'FOREIGN KEY' 
            AND tc.table_name = '{table_name}'
            AND tc.table_schema = 'public'
    """))
    
    outgoing = []
    for row in outgoing_result:
        outgoing.append({
            'constraint_name': row[0],
            'field_name': row[1],
            'related_object': row[2],
            'related_field': row[3],
            'update_rule': row[4],
            'delete_rule': row[5],
            'relationship_type': 'Lookup',
            'cascade_delete': row[5] == 'CASCADE'
        })
    
    # Get incoming relationships (other tables reference this one)
    incoming_result = db.execute(text(f"""
        SELECT 
            tc.constraint_name,
            tc.table_name,
            kcu.column_name,
            ccu.column_name AS referenced_column_name,
            rc.update_rule,
            rc.delete_rule
        FROM information_schema.table_constraints AS tc 
        JOIN information_schema.key_column_usage AS kcu
            ON tc.constraint_name = kcu.constraint_name
        JOIN information_schema.constraint_column_usage AS ccu
            ON ccu.constraint_name = tc.constraint_name
        JOIN information_schema.referential_constraints AS rc
            ON tc.constraint_name = rc.constraint_name
        WHERE tc.constraint_type = 'FOREIGN KEY' 
            AND ccu.table_name = '{table_name}'
            AND tc.table_schema = 'public'
    """))
    
    incoming = []
    for row in incoming_result:
        incoming.append({
            'constraint_name': row[0],
            'related_object': row[1],
            'related_field': row[2],
            'field_name': row[3],
            'update_rule': row[4],
            'delete_rule': row[5],
            'relationship_type': 'Child Relationship',
            'cascade_delete': row[5] == 'CASCADE'
        })
    
    return templates.TemplateResponse("table_relationships.html", {
        "request": request,
        "table_name": table_name,
        "outgoing_relationships": outgoing,
        "incoming_relationships": incoming
    })

@router.get("/api/table-schema/{table_name}")
async def get_table_schema(table_name: str, db: Session = Depends(get_sync_session)):
    """Get detailed schema for a specific table"""
    try:
        # Get column information with detailed metadata
        columns_result = db.execute(text(f"""
            SELECT 
                c.column_name,
                c.data_type,
                c.is_nullable,
                c.column_default,
                c.character_maximum_length,
                CASE WHEN pk.column_name IS NOT NULL THEN true ELSE false END as is_primary_key,
                CASE WHEN fk.column_name IS NOT NULL THEN true ELSE false END as is_foreign_key,
                fk.foreign_table_name,
                fk.foreign_column_name
            FROM information_schema.columns c
            LEFT JOIN (
                SELECT kcu.column_name, kcu.table_name
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu 
                    ON tc.constraint_name = kcu.constraint_name
                WHERE tc.constraint_type = 'PRIMARY KEY'
                    AND tc.table_schema = 'public'
            ) pk ON c.column_name = pk.column_name AND c.table_name = pk.table_name
            LEFT JOIN (
                SELECT 
                    kcu.column_name, 
                    kcu.table_name,
                    ccu.table_name as foreign_table_name,
                    ccu.column_name as foreign_column_name
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu 
                    ON tc.constraint_name = kcu.constraint_name
                JOIN information_schema.constraint_column_usage ccu
                    ON ccu.constraint_name = tc.constraint_name
                WHERE tc.constraint_type = 'FOREIGN KEY'
                    AND tc.table_schema = 'public'
            ) fk ON c.column_name = fk.column_name AND c.table_name = fk.table_name
            WHERE c.table_name = '{table_name}' 
                AND c.table_schema = 'public'
            ORDER BY c.ordinal_position
        """))
        
        columns = []
        for row in columns_result:
            columns.append({
                'name': row[0],
                'type': row[1],
                'nullable': row[2] == 'YES',
                'default': row[3],
                'max_length': row[4],
                'is_primary': row[5],
                'is_foreign': row[6],
                'foreign_table': row[7],
                'foreign_column': row[8]
            })
        
        # Get table row count
        count_result = db.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
        row_count = count_result.scalar()
        
        return {
            "table_name": table_name,
            "columns": columns,
            "row_count": row_count
        }
        
    except Exception as e:
        return {"error": f"Could not fetch schema for {table_name}: {str(e)}"}

@router.get("/admin", response_class=HTMLResponse)
async def admin_panel(request: Request, db: Session = Depends(get_sync_session)):
    """Admin panel for database management"""
    
    # Get database overview
    tables_result = db.execute(text("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        ORDER BY table_name
    """))
    tables = [row[0] for row in tables_result]
    
    # Get recent activity
    try:
        recent_activity = db.execute(text("""
            SELECT 
                'audit_log' as table_name,
                'INSERT' as action,
                created_at,
                user_id
            FROM audit_log 
            ORDER BY created_at DESC 
            LIMIT 10
        """)).fetchall()
    except:
        recent_activity = []
    
    # Get table sizes
    table_stats = {}
    for table in tables:
        try:
            count_result = db.execute(text(f"SELECT COUNT(*) FROM {table}"))
            table_stats[table] = count_result.scalar()
        except:
            table_stats[table] = 0
    
    return templates.TemplateResponse("admin_panel.html", {
        "request": request,
        "tables": tables,
        "table_stats": table_stats,
        "recent_activity": recent_activity,
        "total_tables": len(tables)
    })

@router.get("/admin/{table_name}", response_class=HTMLResponse)
async def admin_table_manager(request: Request, table_name: str, 
                             page: int = 1, search: str = None,
                             db: Session = Depends(get_sync_session)):
    """Admin table management with CRUD operations"""
    
    try:
        # Get table schema
        columns_result = db.execute(text(f"""
            SELECT 
                column_name, 
                data_type, 
                is_nullable,
                column_default,
                CASE WHEN pk.column_name IS NOT NULL THEN true ELSE false END as is_primary
            FROM information_schema.columns c
            LEFT JOIN (
                SELECT kcu.column_name, kcu.table_name
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu 
                    ON tc.constraint_name = kcu.constraint_name
                WHERE tc.constraint_type = 'PRIMARY KEY'
                    AND tc.table_schema = 'public'
            ) pk ON c.column_name = pk.column_name AND c.table_name = pk.table_name
            WHERE c.table_name = '{table_name}' AND c.table_schema = 'public'
            ORDER BY c.ordinal_position
        """))
        columns = [dict(row._asdict()) for row in columns_result]
        
        # Pagination setup
        page_size = 25
        offset = (page - 1) * page_size
        
        # Build search query
        where_clause = ""
        if search:
            search_conditions = []
            for col in columns:
                if col['data_type'] in ['character varying', 'text']:
                    search_conditions.append(f"{col['column_name']} ILIKE '%{search}%'")
            if search_conditions:
                where_clause = f"WHERE {' OR '.join(search_conditions)}"
        
        # Get total count
        count_query = f"SELECT COUNT(*) FROM {table_name} {where_clause}"
        total_records = db.execute(text(count_query)).scalar()
        
        # Get paginated data
        data_query = f"""
            SELECT * FROM {table_name} 
            {where_clause}
            ORDER BY {columns[0]['column_name'] if columns else '1'}
            LIMIT {page_size} OFFSET {offset}
        """
        data_result = db.execute(text(data_query))
        records = [dict(row._asdict()) for row in data_result]
        
        # Calculate pagination info
        total_pages = (total_records + page_size - 1) // page_size
        
        return templates.TemplateResponse("admin_table.html", {
            "request": request,
            "table_name": table_name,
            "columns": columns,
            "records": records,
            "current_page": page,
            "total_pages": total_pages,
            "total_records": total_records,
            "search": search,
            "page_size": page_size
        })
        
    except Exception as e:
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": f"Error managing table {table_name}: {str(e)}"
        })

@router.post("/admin/{table_name}/create")
async def create_record(request: Request, table_name: str, db: Session = Depends(get_sync_session)):
    """Create new record in table"""
    
    try:
        form_data = await request.form()
        
        # Get table columns
        columns_result = db.execute(text(f"""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = '{table_name}' AND table_schema = 'public'
            ORDER BY ordinal_position
        """))
        columns = [row[0] for row in columns_result]
        
        # Build insert query
        insert_columns = []
        insert_values = []
        
        for column in columns:
            if column in form_data and form_data[column].strip():
                insert_columns.append(column)
                insert_values.append(f"'{form_data[column]}'")
        
        if insert_columns:
            insert_query = f"""
                INSERT INTO {table_name} ({', '.join(insert_columns)}) 
                VALUES ({', '.join(insert_values)})
            """
            db.execute(text(insert_query))
            db.commit()
        
        return {"status": "success", "message": "Record created successfully"}
        
    except Exception as e:
        db.rollback()
        return {"status": "error", "message": f"Error creating record: {str(e)}"}

@router.put("/admin/{table_name}/{record_id}")
async def update_record(request: Request, table_name: str, record_id: str, 
                       db: Session = Depends(get_sync_session)):
    """Update existing record"""
    
    try:
        form_data = await request.form()
        
        # Get primary key column
        pk_result = db.execute(text(f"""
            SELECT kcu.column_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu 
                ON tc.constraint_name = kcu.constraint_name
            WHERE tc.constraint_type = 'PRIMARY KEY'
                AND tc.table_name = '{table_name}'
                AND tc.table_schema = 'public'
        """))
        pk_column = pk_result.scalar()
        
        if not pk_column:
            return {"status": "error", "message": "No primary key found"}
        
        # Build update query
        update_sets = []
        for key, value in form_data.items():
            if key != pk_column:
                update_sets.append(f"{key} = '{value}'")
        
        if update_sets:
            update_query = f"""
                UPDATE {table_name} 
                SET {', '.join(update_sets)}
                WHERE {pk_column} = '{record_id}'
            """
            db.execute(text(update_query))
            db.commit()
        
        return {"status": "success", "message": "Record updated successfully"}
        
    except Exception as e:
        db.rollback()
        return {"status": "error", "message": f"Error updating record: {str(e)}"}

@router.delete("/admin/{table_name}/{record_id}")
async def delete_record(request: Request, table_name: str, record_id: str,
                       db: Session = Depends(get_sync_session)):
    """Delete record from table"""
    
    try:
        # Get primary key column
        pk_result = db.execute(text(f"""
            SELECT kcu.column_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu 
                ON tc.constraint_name = kcu.constraint_name
            WHERE tc.constraint_type = 'PRIMARY KEY'
                AND tc.table_name = '{table_name}'
                AND tc.table_schema = 'public'
        """))
        pk_column = pk_result.scalar()
        
        if not pk_column:
            return {"status": "error", "message": "No primary key found"}
        
        # Delete record
        delete_query = f"DELETE FROM {table_name} WHERE {pk_column} = '{record_id}'"
        result = db.execute(text(delete_query))
        db.commit()
        
        if result.rowcount > 0:
            return {"status": "success", "message": "Record deleted successfully"}
        else:
            return {"status": "error", "message": "Record not found"}
        
    except Exception as e:
        db.rollback()
        return {"status": "error", "message": f"Error deleting record: {str(e)}"}

@router.post("/admin/export/csv")
async def export_csv(request: Request, db: Session = Depends(get_sync_session)):
    """Export all database tables as CSV"""
    from fastapi.responses import StreamingResponse
    import io
    import csv
    
    try:
        # Get all tables
        tables_result = db.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name
        """))
        tables = [row[0] for row in tables_result]
        
        # Create CSV content
        output = io.StringIO()
        
        for table in tables:
            # Write table header
            output.write(f"\n# Table: {table}\n")
            
            try:
                # Get column names
                columns_result = db.execute(text(f"""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = '{table}' 
                    AND table_schema = 'public'
                    ORDER BY ordinal_position
                """))
                columns = [row[0] for row in columns_result]
                
                # Get data
                data_result = db.execute(text(f"SELECT * FROM {table} LIMIT 1000"))
                rows = data_result.fetchall()
                
                # Write CSV data
                writer = csv.writer(output)
                writer.writerow(columns)  # Header
                for row in rows:
                    writer.writerow([str(cell) if cell is not None else '' for cell in row])
                
                output.write("\n")  # Separator between tables
                
            except Exception as e:
                output.write(f"Error exporting {table}: {str(e)}\n")
        
        # Prepare response
        output.seek(0)
        content = output.getvalue()
        
        return StreamingResponse(
            io.StringIO(content),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=vectorbid_database_export.csv"}
        )
        
    except Exception as e:
        return {"status": "error", "message": f"Export failed: {str(e)}"}