from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter(tags=["UI"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@router.post("/run", response_class=HTMLResponse)
async def run_pipeline(request: Request, preferences: str = Form(...)):
    pbs_layers = [
        "AVOID PAIRINGS",
        "  IF REPORT < 0800",
        "PREFER PAIRINGS",
        "  IF LAYOVER CITY = 'SAN'",
    ]
    results = {"pbs_layers": pbs_layers}
    return templates.TemplateResponse(
        "results.html", {"request": request, "results": results}
    )
