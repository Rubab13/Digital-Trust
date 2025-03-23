from fastapi import FastAPI, HTTPException, status, Depends
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

SECRET_KEY = "rubab"
serializer = URLSafeTimedSerializer(SECRET_KEY)

app = FastAPI()

app.include_router(customer_router.router, prefix="/customer")
app.include_router(manager_router.router, prefix="/manager")

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

client = AsyncIOMotorClient("mongodb://localhost:27017")
db = client.bank

@app.get("/")
async def index(request: Request):

    # async with db.reviews.find().limit(4) as reviews_cursor:
    #     reviews = await reviews_cursor.to_list(length=None)  
        
    reviews_cursor = db.reviews.aggregate([{"$sample": {"size": 3}}])
    reviews = await reviews_cursor.to_list(length=3)
        
    # async with db.FAQs.find().limit(4) as faqs_cursor:
    #     faqs = await faqs_cursor.to_list(length=None)  
        
    faqs_cursor = db.FAQs.aggregate([{"$sample": {"size": 4}}])
    faqs = await faqs_cursor.to_list(length=4)

    blogs_cursor = db.blogs.find().limit(4)
    blogs = await blogs_cursor.to_list(length=4)

    return templates.TemplateResponse("index.html", {"request": request, "reviews": reviews, "blogs": blogs, "faqs": faqs})

@app.get("/services")
async def index(request: Request):
    return templates.TemplateResponse("services.html", {"request": request})

@app.get("/blog_details{id}")
async def get_blog_details(request:Request, id):  
    flag = await db.blogs.find_one({"title": id})
    return templates.TemplateResponse("blog_details.html", {"request": request, "blog": flag})

@app.get("/blogs", response_class = HTMLResponse)
async def display_blogs(request: Request):

    async with db.blogs.find() as programs_cursor:
        programs = await programs_cursor.to_list(length=None)

    return templates.TemplateResponse("blog.html", {"request": request, "programs": programs})

@app.get("/submit_faq")
async def f(request: Request):
    return {"S":"D"}