import os
import json
import logging
import uvicorn # FastAPI 실행
import certifi
from models import User
from jose import JWTError, jwt
from auth import get_current_user
from create import main as create_main
from datetime import datetime, timedelta
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi import FastAPI, Depends, HTTPException, status, Request, Query
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from passlib.context import CryptContext
from pymongo.errors import DuplicateKeyError
from motor.motor_asyncio import AsyncIOMotorClient

from schemas import UserCreate, UserInDB, Token, UserIDSearchRequest, UserPWSearchRequest, Result, UserUpdateRequest

templates = Jinja2Templates(directory="templates")
app = FastAPI()

# Security settings
SECRET_KEY = "secret_key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

Json_file_path = 'json/job.json'

def load_allowed_job_categories():
    with open(Json_file_path, 'r', encoding='utf-8') as file:
        return json.load(file)
    
allowed_job_category = load_allowed_job_categories()

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# SSL 인증서 파일 경로 설정
ca = certifi.where()

# MongoDB 연결 설정
MONGO_DETAILS = os.getenv("MONGO_DETAILS", "mongodb+srv://zzcv00:지
@app.get("/job_info")
async def get_job_info(request: Request):
    return templates.TemplateResponse("job_info.html", {"request": request})

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# 메인 페이지
@app.get("/main")
async def read_root(request: Request):
    return templates.TemplateResponse("main.html", {"request": request})

# MBTI/직무 선택
@app.get("/api/selection")
async def get_selection(mbti: str, jobCategory: str):
    logging.info(f'Received MBTI: {mbti}, Job Category: {jobCategory}')
    if jobCategory not in allowed_job_category:
        raise HTTPException(status_code=400, detail="Invalid Job Category")
    # 요청받은 MBTI와 Job Category를 그대로 반환
    return {"mbti": mbti, "jobCategory": jobCategory}

# MBTI/직무 선택 페이지
@app.get("/selection", response_class=HTMLResponse)
async def selection_form(request: Request):
    return templates.TemplateResponse("selection.html", {"request": request})

# 로딩 페이지
@app.get("/loading", response_class=HTMLResponse)
async def get_loading(request: Request):
    return templates.TemplateResponse("loading.html", {"request": request})

# 결과
@app.get("/api/result", response_model=Result)
def get_result(mbti: str = Query(...), jobcategory: str = Query(...)):
    try:
        result = create_main(mbti, jobcategory)
        
        if isinstance(result, dict):  # 결과가 딕셔너리인 경우
            return result
        else:
            raise HTTPException(status_code=500, detail="Unexpected result format")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 결과 페이지
@app.get("/result", response_class=HTMLResponse)
async def show_result(request: Request, mbti: str, jobCategory: str):
    return templates.TemplateResponse("result.html", {"request": request, "mbti":mbti, "jobcategory":jobCategory})

# 내 정보
@app.get("/api/users/me", response_model=UserInDB)
async def get_user_info(current_user: UserInDB = Depends(get_current_user)):
    return current_user


# Static files serving
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# 로그인 페이지
@app.get("/", response_class=HTMLResponse)
async def read_index(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

# 회원가입 페이지
@app.get("/join_in", response_class=HTMLResponse)
async def get_join_in(request: Request):
    return templates.TemplateResponse("join_in.html", {"request": request})

# 마이페이지
@app.get("/mypage", response_class=HTMLResponse)
async def get_mypage(request: Request):
    return templates.TemplateResponse("mypage.html", {"request": request})

# 회원 정보 수정 페이지
@app.get("/info_edit", response_class=HTMLResponse)
async def get_info_edit(request: Request):
    return templates.TemplateResponse("info_edit.html", {"request": request})

# 아이디 찾기 페이지
@app.get("/id_search", response_class=HTMLResponse)
async def get_id_search(request: Request):
    return templates.TemplateResponse("id_search.html", {"request": request})

# 비밀번호 찾기 페이지
@app.get("/pw_search", response_class=HTMLResponse)
async def get_pw_search(request: Request):
    return templates.TemplateResponse("pw_search.html", {"request": request})

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
