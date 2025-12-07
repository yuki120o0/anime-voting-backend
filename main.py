from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import create_tables
from auth import router as auth_router
from protected_voting import router as voting_router  
from admin_api import router as admin_router
from user_profile import router as user_router
from search import router as search_router

# 创建数据库表
create_tables()

# 创建FastAPI应用
app = FastAPI(
    title="动漫投票系统",
    description="一个基于FastAPI和html的动漫投票系统",
    version="1.0.0"
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 前端开发服务器
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(auth_router)
app.include_router(voting_router)  
app.include_router(admin_router)
app.include_router(user_router)
app.include_router(search_router)

@app.get("/")
async def root():
    return {"message": "欢迎使用动漫投票系统 API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "服务运行正常"}



