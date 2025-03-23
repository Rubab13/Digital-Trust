from fastapi import APIRouter, Depends
from fastapi import FastAPI, HTTPException, status
from routes import customer_router, manager_router
from fastapi.responses import JSONResponse
import motor
from motor.motor_asyncio import AsyncIOMotorClient
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from itsdangerous import URLSafeTimedSerializer, BadSignature
import hashlib
import bson
from bson import ObjectId
from datetime import datetime

router = APIRouter()

templates = Jinja2Templates(directory="templates")
client = AsyncIOMotorClient("mongodb://localhost:27017")
db = client.bank

SECRET_KEY = "rubab"
serializer = URLSafeTimedSerializer(SECRET_KEY)

@router.get("/manager-signin", response_class=HTMLResponse)
async def manager_login_form(request: Request):
    return templates.TemplateResponse("manager-signin.html", {"request": request})

@router.post("/manager-signin", response_class=HTMLResponse)
async def manager_login_submit(request: Request, email: str = Form(...), password: str = Form(...)):
    
    flag = await db.manager.find_one({"email": email})
    if flag and flag.get("password") == password:
        response = RedirectResponse(url="/manager/manager", status_code=status.HTTP_303_SEE_OTHER)

    else:
        return HTMLResponse("""
            <script>
                alert("Invalid email or password. Please try again.");
                window.location.href = "/manager-signin";
            </script>
        """)

    session_data = {"email": str(flag["email"])}
    session_cookie = serializer.dumps(session_data)
    response.set_cookie("session", session_cookie)
    return response

@router.get("/manager", response_class = HTMLResponse)
async def manager(request: Request):

    session_cookie = request.cookies.get("session")
    if not session_cookie:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    try:
        session_data = serializer.loads(session_cookie)
        em = session_data["email"]

    except:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    manager_data = await db.manager_data.find_one({"email": em})
    customer_data = await db.customer_data.find().to_list(length=None)
    top_customers = await db.customer_data.find().sort("current_balance", -1).limit(5).to_list(length=None)


    return templates.TemplateResponse("manager.html", {"request": request, "data": manager_data, "customer_data": customer_data, "top_customers": top_customers})

@router.get("/manager-logout")
async def logout():
    response = RedirectResponse(url="/manager/manager-signin")
    response.delete_cookie("session")
    return response

@router.post("/delete_user/{account_number}")
async def func(account_number: str): 
    deleted_customer = await db.customer_data.delete_one({"account_number": account_number})

    if deleted_customer.deleted_count == 1:
        return HTMLResponse("""
            <script>
                alert("Customer delted.");
                window.location.href = "/manager/manager";
            </script>
        """)    
    else:
        # raise HTTPException(status_code=404, detail=f"Customer with account number {account_number} not found or deletion failed")
        return HTMLResponse("""
            <script>
                alert("Customer not found.");
                window.location.href = "/manager";
            </script>
        """)
        
@router.post("/search_customer", response_class=HTMLResponse)
async def search_customer(request: Request, search_customer: str = Form(...)):
    customer_data = await db.customer_data.find_one({"account_number": search_customer})
    
    if customer_data:
        customer_data['_id'] = str(customer_data['_id'])
        return JSONResponse(content=customer_data)
    else:
        return JSONResponse(content={"error": "Customer not found"}, status_code=status.HTTP_404_NOT_FOUND)
