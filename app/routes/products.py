# app/routes/products.py
from pathlib import Path
from fastapi import APIRouter
from fastapi.responses import FileResponse

router = APIRouter()

@router.get("/")
async def serve_products_page():
    """Products overview page"""
    products_path = Path(__file__).parent.parent / "static" / "pages" / "products" / "index.html"
    if products_path.exists():
        return FileResponse(products_path)
    return {"message": "Products page coming soon"}

@router.get("/bid-optimizer")
async def serve_bid_optimizer_page():
    """Bid Optimizer product page"""
    bid_optimizer_path = Path(__file__).parent.parent / "static" / "pages" / "products" / "bid-optimizer.html"
    if bid_optimizer_path.exists():
        return FileResponse(bid_optimizer_path)
    return {"message": "Bid Optimizer page coming soon"}

@router.get("/route-analyzer")
async def serve_route_analyzer_page():
    """Route Analyzer product page"""
    route_analyzer_path = Path(__file__).parent.parent / "static" / "pages" / "products" / "route-analyzer.html"
    if route_analyzer_path.exists():
        return FileResponse(route_analyzer_path)
    return {"message": "Route Analyzer page coming soon"}

@router.get("/schedule-builder")
async def serve_schedule_builder_page():
    """Schedule Builder product page"""
    schedule_builder_path = Path(__file__).parent.parent / "static" / "pages" / "products" / "schedule-builder.html"
    if schedule_builder_path.exists():
        return FileResponse(schedule_builder_path)
    return {"message": "Schedule Builder page coming soon"}

@router.get("/pattern-intelligence")
async def serve_pattern_intelligence_page():
    """Pattern Intelligence product page"""
    pattern_intelligence_path = Path(__file__).parent.parent / "static" / "pages" / "products" / "pattern-intelligence.html"
    if pattern_intelligence_path.exists():
        return FileResponse(pattern_intelligence_path)
    return {"message": "Pattern Intelligence page coming soon"}

@router.get("/mobile")
async def serve_mobile_page():
    """Mobile App product page"""
    mobile_path = Path(__file__).parent.parent / "static" / "pages" / "products" / "mobile.html"
    if mobile_path.exists():
        return FileResponse(mobile_path)
    return {"message": "Mobile App page coming soon"}