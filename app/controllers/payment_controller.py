from fastapi import APIRouter, Depends 
from fastapi.responses import JSONResponse
from starlette.templating import Jinja2Templates

from app.middlewares.jwt_handler import JWTBearer
from app.stripe_integration.stripe_products import get_payment_links

templates = Jinja2Templates(directory="app/templates")
router = APIRouter(
    prefix="/payments",
    tags=["payments"]
)
 
@router.get("/payment_links", tags=['payment_links'], status_code=200, dependencies=[Depends(JWTBearer())])
async def get_all_payment_links():
    response = await get_payment_links()
    return JSONResponse(status_code=200, content=response)