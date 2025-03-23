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

@router.get("/customer-signin", response_class = HTMLResponse)
def customer_signin(request: Request):
    return templates.TemplateResponse("customer-signin.html", {"request": request})

@router.post("/customer-signin", response_class=HTMLResponse)
async def customer_login_form_submit(request: Request, email: str = Form(...), password: str = Form(...)):
    
    if not email.strip() or not password.strip():
        return RedirectResponse(url="/customer/customer-signin", status_code=status.HTTP_303_SEE_OTHER)
    
    data = await db.customer_data.find_one({"email": email})
    
    if data and data.get("password") == password:
        
        response = RedirectResponse(url="/customer/customer", status_code=status.HTTP_303_SEE_OTHER)
        
        session_customer_email = {"email": str(data["email"])}
        session_customer_account_number = {"account_number": str(data["account_number"])}

        session_cookie_customer_email = serializer.dumps(session_customer_email)
        session_cookie_customer_account_number = serializer.dumps(session_customer_account_number)

        response.set_cookie("session_customer_email", session_cookie_customer_email)
        response.set_cookie("session_customer_account_number", session_cookie_customer_account_number)

        return response
    
    else:
        return HTMLResponse("""
            <script>
                alert("Invalid email or password. Please try again.");
                window.location.href = "/customer-signin";
            </script>
        """)
    
    # else:
    #     raise HTTPException(status_code=400, detail="Invalid email or password")

@router.get("/customer", response_class = HTMLResponse)
async def customer(request: Request):

    session_cookie1 = request.cookies.get("session_customer_email")
    session_cookie2 = request.cookies.get("session_customer_account_number")

    if not session_cookie1 or not session_cookie2:
        return RedirectResponse(url="/customer-signin", status_code=status.HTTP_303_SEE_OTHER)

    try:
        session_data1 = serializer.loads(session_cookie1)
        em = session_data1["email"]

        session_data2 = serializer.loads(session_cookie2)
        account = session_data2["account_number"]

        # return templates.TemplateResponse("customer.html", {"request": request, "email": em})
    
    except:
        return RedirectResponse(url="/customer-signin", status_code=status.HTTP_303_SEE_OTHER)


    customer_data = await db.customer_data.find_one({"email": em})

    transaction_data = await db.transactions_data.find({"$or": [
        { "sender_account_number": account },
        { "receiver_account_number": account }
    ]}).to_list(length=None)

    return templates.TemplateResponse("customer.html", {"request": request, "customer_data": customer_data, "transaction_data": transaction_data})

@router.get("/customer-signup", response_class = HTMLResponse)
def customer_sign_up(request: Request):
    return templates.TemplateResponse("customer-signup.html", {"request": request})

@router.post("/update_customer_data")
async def update_customer_data(
    request: Request,
    email_from_update_customer: str = Form(""),
    phone_from_update_customer: str = Form(""),
    address_from_update_customer: str = Form("")
):
    session_cookie2 = request.cookies.get("session_customer_account_number")

    if not session_cookie2:
        return RedirectResponse(url="/customer-signin", status_code=status.HTTP_303_SEE_OTHER)

    try:
        session_data2 = serializer.loads(session_cookie2)
        account = session_data2["account_number"]
    except:
        return RedirectResponse(url="/customer-signin", status_code=status.HTTP_303_SEE_OTHER)

    update_data = {}
    if email_from_update_customer:
        update_data["email"] = email_from_update_customer
    if phone_from_update_customer:
        update_data["phone"] = phone_from_update_customer
    if address_from_update_customer:
        update_data["address"] = address_from_update_customer

    if update_data:
        await db.customer_data.update_one(
            {"account_number": account},
            {"$set": update_data}
        )
        
    transaction_data = await db.transactions_data.find({"$or": [
            { "sender_account_number": account },
            { "receiver_account_number": account }
    ]}).to_list(length=None)
        
    customer = await db.customer_data.find_one({"account_number": account})    
    
    return templates.TemplateResponse("customer.html", {"request": request, "customer_data": customer, "transaction_data": transaction_data})

    # return {"message": "Customer data updated successfully"}

@router.post("/customer-signup", response_class=HTMLResponse)
async def abc(
    request: Request,
    first_name: str = Form(...),
    last_name: str = Form(...),
    email: str = Form(...),
    phone: str = Form(...),
    address: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...),
    day: int = Form(...),
    month: int = Form(...),
    year: int = Form(...),
):
    
    dictionary = await db.customer_data.find().to_list(length = None)
    
    numerical_parts = [
        int(customer['account_number'].replace('account', ''))
        for customer in dictionary if 'account_number' in customer
    ]

    max_account_number = max(numerical_parts)
    account_number_to_give = max_account_number + 1
    
    format_length = len(str(max_account_number))

    new_account_number = f"account{account_number_to_give:0{format_length}d}"

    birth_date = f"{year:04d}-{month:02d}-{day:02d}"
    
    bd = datetime(year, month, day)
    today = datetime.today()
    age = today.year - bd.year - ((today.month, today.day) < (bd.month, bd.day))

    customer = {
        "account_number": new_account_number,
        "name": first_name + " " + last_name,
        "email": email,
        "phone": phone,
        "address": address,
        "password": password,
        "birth_date": birth_date,
        "age": str(age),
        "image": "user.png",
        "current_balance": "0",
    }

    result = await db.customer_data.insert_one(customer)
    
    customer_data = await db.customer_data.find_one({"account_number": new_account_number})

    response =  templates.TemplateResponse("customer.html", {"request": request, "customer_data": customer_data})
    
    session_data = {"account_number": str(new_account_number)}
    session_cookie = serializer.dumps(session_data)
    response.set_cookie("session_customer_account_number", session_cookie)
    
    return response
    
    # return HTMLResponse(f"""
    #         <script>
    #             alert(`inserted`);
    #         </script>
    # """)

@router.post("/dep")
async def funnc(request: Request, deposition_amount: str = Form(...), deposit_password: str = Form(...)):

    session_cookie1 = request.cookies.get("session_customer_account_number")

    if not session_cookie1:
        return RedirectResponse(url="/customer-signin", status_code=status.HTTP_303_SEE_OTHER)

    try:
        session_data1 = serializer.loads(session_cookie1)
        acc = session_data1["account_number"]

    except:
        return RedirectResponse(url="/customer-signin", status_code=status.HTTP_303_SEE_OTHER)

    customers = await db.customer_data.find_one({"account_number": acc})

    if customers["password"] == deposit_password:
                
        amount = int(deposition_amount)
        x = int(customers["current_balance"]) + amount
        
        await db.customer_data.update_one(
            {"account_number": acc},
            {"$set": {"current_balance": str(x)}}
        )
        
        transaction_data = await db.transactions_data.find({"$or": [
            { "sender_account_number": acc },
            { "receiver_account_number": acc }
        ]}).to_list(length=None)
        
        return templates.TemplateResponse("customer.html", {"request": request, "customer_data": customers, "transaction_data": transaction_data})

    return HTMLResponse(f"""
            <script>
                alert(`You entered the wrong password. For safety reasons, we are redirecting you to the sign in page.`);
                window.location.href = "/customer-signin";
            </script>
    """)

@router.post("/with")
async def funnc(request: Request, withdraw_amount: str = Form(...), withdraw_password: str = Form(...)):

    session_cookie1 = request.cookies.get("session_customer_account_number")

    if not session_cookie1:
        return RedirectResponse(url="/customer-signin", status_code=status.HTTP_303_SEE_OTHER)

    try:
        session_data1 = serializer.loads(session_cookie1)
        acc = session_data1["account_number"]

    except:
        return RedirectResponse(url="/customer-signin", status_code=status.HTTP_303_SEE_OTHER)

    customers = await db.customer_data.find_one({"account_number": acc})

    flag = False
    
    if customers["password"] == withdraw_password:
                
        amount = int(withdraw_amount)
        x = int(customers["current_balance"]) - amount
        
        if x >= 0:
            await db.customer_data.update_one(
                {"account_number": acc},
                {"$set": {"current_balance": str(x)}}
            )
        else:
            flag = True
        
        transaction_data = await db.transactions_data.find({"$or": [
            { "sender_account_number": acc },
            { "receiver_account_number": acc }
        ]}).to_list(length = None)
        
        
        return templates.TemplateResponse("customer.html", {"request": request, "customer_data": customers, "transaction_data": transaction_data, "withdraw_flag": flag})

    # return RedirectResponse(url="/customer-signin", status_code=status.HTTP_303_SEE_OTHER)
    return HTMLResponse(f"""
            <script>
                alert(`You entered the wrong password. For safety reasons, we are redirecting you to the sign in page.`);
                window.location.href = "/customer-signin";
            </script>
    """)

@router.get("/customer-logout")
async def logout():
    response = RedirectResponse(url="/customer-signin")
    response.delete_cookie("session_customer_account_number")
    response.delete_cookie("session_customer_email")
    return response
