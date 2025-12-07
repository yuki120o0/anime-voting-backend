from sqlalchemy import create_engine,UniqueConstraint
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column ,Integer,String,Text,Float,Boolean,DateTime,JSON
from datetime import datetime, timezone

#1.数据库连接配置
SQLALCHEMY_DATABASE_URL="sqlite:///./anime_voting.db"

#2.创建数据库引擎
engine = create_engine(SQLALCHEMY_DATABASE_URL,connect_args={"check_same_thread":False})
# check_same_thread 是 SQLite 的一个连接参数，用于控制是否检查数据库连接是否在同一个线程中使用
# 其默认值为True，即在SQLite中默认数据库仅能有一个线程
# 设置为False，则能同时连接多个线程


#3.创建会话工厂
SessionLocal = sessionmaker(autocommit=False,autoflush=False,bind=engine)

#4.创建基类
Base=declarative_base()

# Column函数
Column(
    Integer, # 数据类型
    primary_key = True, # 是否主键
    index = True,       # 是否创建索引
    unique = True,      # 是否唯一
    nullable = False,   # 是否可为空
    default = "默认值"   # 默认值
)

# 创建用户表
class User(Base):
    __tablename__ = "users" # 数据库中的实际表名

    # 主键字段
    id = Column(Integer,primary_key=True,index=True)

    # 用户信息字段
    username = Column(String(50),unique=True,nullable=False)
    password_hash = Column(String(50),nullable=False)
    role = Column(String(50),default="guest")

    # 时间戳
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


# 创建投票
class VotingSession(Base):
    __tablename__="__voting_session__"
    
    # 主键
    id = Column(Integer,primary_key=True,index=True)

    # 基本信息
    

    master_id=Column(Integer,nullable=False)

    is_public=Column(Boolean,default=True)

    title=Column(String(100),nullable=False)
    
    description = Column(String(1000))

    # 动漫相关信息
    anime_list = Column(JSON,default=[])

    # 时间戳
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # 投票设计字段
    allow_multiple_votes = Column(Boolean,default=True)
    max_votes_per_user = Column(Integer,default=1000) 



class Vote(Base):
    __tablename__="__votes__"

    id = Column(Integer,primary_key=True,index=True)

    session_id=Column(Integer,nullable=False)
    voted_anime=Column(JSON,nullable=False)
    user_id = Column(Integer,nullable=False)

    # 唯一约束 :同一用户在同一会话中只能投一次票
    __table_args__ = (UniqueConstraint("session_id", "user_id", name="uix_session_user"),)
    # __table_args__：SQLAlchemy 的特殊属性，用于定义表级别的参数（如约束、索引等）

    # UniqueConstraint：唯一约束类，确保指定列的组合值在表中是唯一的

    # "session_id", "user_id"：约束涉及的列名

    # name="uix_session_user"：约束的名称（在数据库中显示的名称）
    

    # 时间戳
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
# 在 models.py 中添加认证相关模型
from pydantic import BaseModel
from typing import Optional

class UserRegister(BaseModel):
    """用户注册模型"""
    username: str
    password: str
    role: str = "guest"

class UserLogin(BaseModel):
    """用户登录模型"""
    username: str
    password: str

class Token(BaseModel):
    """令牌响应模型"""
    access_token: str
    token_type: str

class TokenData(BaseModel):
    """令牌数据模型"""
    username: Optional[str] = None
    user_id: Optional[int] = None

class SessionCreate(BaseModel):
    """会话创建模型"""
    title: str
    description: Optional[str] = None,
    is_public: bool = True,
    allow_multiple_votes: bool = True,
    max_votes_per_user: int = 1000

class AddAnime(BaseModel):
    session_id: int
    bangumi_id: int

class CastVote(BaseModel):
    session_id: int
    voted_anime: list
   

# 投票设定
VOTE_LEVELS={
    "bad":{"lable":"卧槽，柿！！！","score":-1},
    "poor":{"lable":"杂鱼","score":1},
    "justsoso":{"lable":"平庸","score":2},
    "good":{"lable":"值得一看","score":3},
    "great":{"lable":"佳作必看","score":4},
    "god":{"lable":"神中神","score":6}
}


# 创建表的函数
def create_tables():
    Base.metadata.create_all(bind=engine)

# 获取数据库会话的函数
def get_db():
    """
    获取数据库会话（用于依赖注入）
    在Web框架中为每个请求提供独立的Session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
if __name__=="__main__":
    create_tables()



    
