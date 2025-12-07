
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta,timezone
from typing import Optional
import os

# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"],deprecated="auto")# 定义一个类
                # CryptContext
                    # 来自 passlib 库的类，用于管理密码哈希
                    # 提供统一的接口来处理密码的加密和验证

                # schemes=["bcrypt"]
                    # 指定使用的加密算法为 bcrypt
                    # bcrypt 是一种安全的密码哈希函数，专门为密码存储设计
                    # 它会自动处理盐值(salt)，防止彩虹表攻击

                # deprecated="auto"
                    # 自动标记不推荐使用的算法（如果有的话）
                    # 在这里只用了 bcrypt，所以没有不推荐的算法

# JWT配置
SECRET_KEY = os.getenv("JWT_SECRET_KEY","your-secret-key-for-development")  # 在生产环境中应该使用环境变量
    # SECRET_KEY - 密钥
    # 作用：
    # 签名令牌：用于对 JWT 进行数字签名，防止篡改
    # 验证令牌：验证接收到的令牌是否由合法服务器签发
ALGORITHM = "HS256"
    # ALGORITHM - 算法
    # 含义：
    # HS256 = HMAC with SHA-256
    # 使用对称加密算法，用同一个密钥进行签名和验证
ACCESS_TOKEN_EXPIRE_MINUTES = 300
    # ACCESS_TOKEN_EXPIRE_MINUTES - 令牌有效期
    # 作用：
    # 设置访问令牌的有效时间（30分钟）
    # 过期后用户需要重新登录或刷新令牌

class PasswordUtils:
    """密码工具类"""
    
    @staticmethod
    def hash_password(password: str) -> str: # -> 返回值类型
        """加密密码"""
        return pwd_context.hash(password) 
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """验证密码"""
        return pwd_context.verify(plain_password,hashed_password)
    
    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):# data: dict - 要编码到令牌中的数据
                                      # expires_delta: Optional[timedelta] - 可选的过期时间增量
        """创建JWT访问令牌"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(timezone.utc)+ expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp":expire})
        encoded_jwt = jwt.encode(to_encode,SECRET_KEY,algorithm=ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    def verify_token(token: str):
        """验证JWT令牌"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except JWTError:
            return None
    @staticmethod
    def get_username_from_token(token:str):
        """从令牌中获取用户名"""
        payload = PasswordUtils.verify_token(token)
        if payload:
            return payload.get("sub") # sub是标准JWT字段，表示subject（主体）
        return None
        

#JWT令牌组成：
#- Header（头部）：算法和类型
#- Payload（载荷）：用户数据
#- Signature（签名）：防篡改验证

#令牌验证流程：
#1. 客户端发送令牌
#2. 服务器验证签名
#3. 提取用户信息
#4. 授权访问资源

#encode(): 使用 algorithm=ALGORITHM （单数，字符串）

#decode(): 使用 algorithms=[ALGORITHM] （复数，列表）