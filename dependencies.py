from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from database import get_db,User
from security import PasswordUtils
from crud import UserCRUD

security = HTTPBearer()
# HTTPBearer 来自 fastapi.security.http 模块（如果你使用的是FastAPI框架）或者类似的安全工具。它用于在API请求中检查Authorization头，确保其包含一个Bearer Token。

# 当你在代码中写下 security = HTTPBearer()，你创建了一个安全依赖项，它可以用在FastAPI的路由中来自动验证请求的授权头。

# 具体来说，当请求到达时，HTTPBearer 会检查请求头中的Authorization字段，该字段的值应该是 Bearer <token> 格式。如果找不到授权头，或者格式不正确（比如没有Bearer关键字），它将自动返回401未授权错误。

# 如果令牌存在且格式正确，那么该令牌会被提取出来，并可以在视图函数中作为参数使用。

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    # credentials: 变量名，用于接收认证信息

    # HTTPAuthorizationCredentials: 类型注解，表示这是一个认证凭证对象

    # Depends(security): 依赖注入，告诉 FastAPI 使用 security 实例来处理认证
    db: Session = Depends(get_db)
):
    """获取当前用户依赖项"""
    token = credentials.credentials
    payload = PasswordUtils.verify_token(token)
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的令牌",
            headers={"WWW-Authenticate": "Bearer"}
        )
    # status_code: 使用HTTP状态码401表示未授权。
    # detail: 错误详情，这里用中文表示"无效的令牌"。
    # headers: 设置了一个WWW-Authenticate头部，值为"Bearer"，这告诉客户端应该使用Bearer令牌认证方式。
    
    username: str = payload.get("sub")
    user_id: int = payload.get("user_id")
    
    if username is None or user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的令牌数据"
        )
    
    user = UserCRUD.get_user_by_id(db, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在"
        )
    
    return user

# 添加管理员权限
async def get_current_admin(current_user:User =Depends(get_current_user)):
    """检查当前用户是否为管理员"""
    if current_user.role!="admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="需要管理员权限")
    return current_user

def require_admin(required_role:str):
    """要求特定角色的依赖项工场函数"""
    async def role_checker(current_user:User = Depends(get_current_user)):
        if current_user.role != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"需要{required_role}角色权限"
            )
        return current_user # 为什么返回user，不返回空
    
    return role_checker #为什么返回这个函数

async def require_user(current_user:User = Depends(get_current_user)):
    """要求普通用户权限"""
    if current_user.role not in ["user",'admin']:
        raise HTTPException(
            status_code = status.HTTP_403_FORBIDDEN,
            detail = "需要用户权限"
        )
    return current_user

def require_ownership(resource_owmer_id:int):
    """检查当前用户是否为资源所有者"""
    async def ownership_checker(current_user:User = Depends(get_current_user)):
        if current_user.id!=resource_owmer_id and current_user.role != "admin":
             raise HTTPException(
            status_code = status.HTTP_403_FORBIDDEN,
            detail = "无权访问此资源"
        )
        return current_user
    return ownership_checker