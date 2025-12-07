from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta

from database import get_db
from security import PasswordUtils
from crud import UserCRUD
from database import UserRegister, Token, User
from dependencies import get_current_user
from fastapi.responses import JSONResponse

router= APIRouter(prefix = "/auth",tags = ["认证"])
# prefix="/auth"
# 路径前缀：所有在这个 router 中定义的路由都会自动添加这个前缀
# 例如：/login 会变成 /auth/login
# tags=["认证"]
# API 文档标签：在 Swagger UI 文档中将这些路由分组显示
# 提高文档的可读性和组织性
@router.post("/register", response_model=dict)
# response_model=dict
# 响应模型：指定接口返回的数据结构

# 作用：

# 数据验证和序列化

# API 文档生成

# 自动过滤返回字段
async def register(user_data: UserRegister, db: Session = Depends(get_db)):
    """用户注册"""
    result = UserCRUD.register_user(db, user_data)
    try:  
        if result is None:
                return JSONResponse(
                    content={"error": "用户名或邮箱已存在"}, 
                    status_code=400
                )
            
            # 如果创建成功，返回用户信息（排除密码）
        return {
                "id": result.id,
                "username": result.username,
                "created_at": result.created_at
            }
            
    except Exception as e:
        return JSONResponse(
            content={"error": f"注册失败: {str(e)}"}, 
            status_code=500
        )

@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
#     OAuth2PasswordRequestForm 是一个 FastAPI 内置的类，专门用于处理 OAuth2 密码授权模式的登录请求。它会自动从请求的 form-data 中提取以下字段：

# username (必需): 用户名

# password (必需): 密码

# scope (可选): 权限范围

# client_id (可选): 客户端ID

# client_secret (可选): 客户端密钥
    """用户登录"""
    user = UserCRUD.authenticate_user(db, form_data.username, form_data.password)
    
    if user is None:
                return JSONResponse(
                    content={"error": "账号或密码错误"}, 
                    status_code=400
                )
    
    access_token_expires = timedelta(minutes=30)
    access_token = PasswordUtils.create_access_token(
        data={"sub": user.username, "user_id": user.id},
        expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me")
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "username": current_user.username,
        "role": current_user.role,
        "created_at": current_user.created_at
    }

@router.post("/change_password")
async def change_password(
    old_password:str,
    new_password:str,
    current_user:User = Depends(get_current_user),
    db:Session=Depends(get_db)
):
    """修改密码"""
    result = UserCRUD.change_password(db,current_user.id,old_password,new_password)
    if "error" in result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail = result["error"]
        )
    return {"message":"密码修改成功"}