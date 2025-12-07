from sqlalchemy.orm import Session
from database import VotingSession,User,Vote,VOTE_LEVELS
from sqlalchemy.orm.attributes import flag_modified
from datetime import datetime, timezone

        
# class VotingSessionCRUD:
#     @staticmethod
#     def create_session(db:Session,master_id:int,is_public:bool,title:str):
#         session=VotingSession(master_id=master_id,is_public=is_public,title=title)
#         try:
#             db.add(session)
#             db.commit()
#             db.refresh(session)
#             print(f"动漫投票会话创建成功，会话名：{title}(ID:{session.id})")
#             return session
#         except Exception as e:
#             db.rollback()
#             print(f"创建会话失败：{e}")
#             return None
        
#     from sqlalchemy.orm.attributes import flag_modified

#     @staticmethod
#     def add_anime_to_session(db: Session, session_id: int, anime_data: dict):
#         session = db.query(VotingSession).filter(VotingSession.id == session_id).first()
#         try:
#             if not session:
#                 print(f"未找到ID为{session_id}的投票会话")
#                 return None
            
#             # 确保 anime_list 已初始化
#             if session.anime_list is None:
#                 session.anime_list = []
            
#             # 检查动漫是否已存在（基于标题）
#             anime_title = anime_data.get("title")
#             anime_exists = False
            
#             for existing_anime in session.anime_list:
#                 if existing_anime.get("title") == anime_title:
#                     anime_exists = True
#                     break
            
#             if not anime_exists:
#                 # 创建新的列表（确保触发变更检测）
#                 new_anime_list = session.anime_list.copy()  # 或者 list(session.anime_list)
#                 new_anime_list.append(anime_data)
#                 session.anime_list = new_anime_list
                
#                 # 明确标记字段已修改
#                 flag_modified(session, "anime_list")
                
#                 db.commit()
#                 db.refresh(session)
#                 print(f"成功添加动漫: {anime_data}")
#             else:
#                 print(f"动漫 '{anime_title}' 已存在")
            
#             return session   
                
#         except Exception as e:
#             db.rollback()
#             print(f"错误：{e}")
#             return None
                
    
#     @staticmethod
#     def get_all_animes(db:Session,session_id:int):
        
#         session = db.query(VotingSession).filter(session_id==VotingSession.id).first()
#         if not session:
#             return None
#         try:
#             return session.anime_list
#         except Exception as e:
#             db.rollback()
#             print(f"错误{e}")
#             return None


from security import PasswordUtils
from database import User, UserRegister, UserLogin

class UserCRUD:
    """用户相关数据库操作 - 扩展认证功能"""
    
    @staticmethod
    def register_user(db: Session, user_data: UserRegister):
        """用户注册"""
        try:
            # 检查用户名是否已存在
            existing_user = UserCRUD.get_user_by_username(db, user_data.username)
            if existing_user:
                return None
            
            # 加密密码
            hashed_password = PasswordUtils.hash_password(user_data.password)
            
            # 创建用户
            user = User(
                username=user_data.username,
                password_hash=hashed_password,
                role=user_data.role
            )
            
            db.add(user)
            db.commit()
            db.refresh(user)
            
            print(f"✅ 用户注册成功: {user_data.username} (ID: {user.id})")
            return user
            
        except Exception as e:
            db.rollback()
            print(f"❌ 用户注册失败: {e}")
            return None
    
    @staticmethod
    def authenticate_user(db: Session, username: str, password: str):
        """用户认证"""
        user = UserCRUD.get_user_by_username(db, username)
        if not user:
            return None
        
        if not PasswordUtils.verify_password(password, user.password_hash):
            return None
        
        return user
    
    @staticmethod
    def change_password(db: Session, user_id: int, old_password: str, new_password: str):
        """修改密码"""
        try:
            user = UserCRUD.get_user_by_id(db, user_id)
            if not user:
                return {"error": "用户不存在"}
            
            # 验证旧密码
            if not PasswordUtils.verify_password(old_password, user.password_hash):
                return {"error": "旧密码错误"}
            
            # 更新密码
            user.password_hash = PasswordUtils.hash_password(new_password)
            db.commit()
            
            print(f"✅ 用户 {user.username} 密码修改成功")
            return {"message": "密码修改成功"}
            
        except Exception as e:
            db.rollback()
            print(f"❌ 密码修改失败: {e}")
            return {"error": "密码修改失败"}
   # 在 UserCRUD 类中添加完整的登录方法
    @staticmethod
    def login_user(db: Session, username: str, password: str):
        """用户登录并返回令牌"""
        auth_result = UserCRUD.authenticate_user(db, username, password)
        
        if not auth_result:
            return {"error":"用户名或密码错误"}
        
        user = auth_result
        
        # 创建访问令牌 
        access_token = PasswordUtils.create_access_token(
            data={"sub": user.username, "user_id": user.id}
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user_id": user.id,
            "username": user.username
        }

    @staticmethod
    def get_user_by_username(db: Session, username: str):
        """根据用户名获取用户"""
        return db.query(User).filter(User.username == username).first()
    
    @staticmethod
    def get_user_by_id(db: Session, user_id: int):
        """根据ID获取用户"""
        return db.query(User).filter(User.id == user_id).first()
    
    @staticmethod
    def get_all_users(db: Session, skip: int = 0):
        """获取所有用户"""
        return db.query(User).offset(skip).all()
    
class VotingSessionCRUD:
    """投票会话相关操作"""
    
    @staticmethod
    def create_session(db: Session, title: str, master_id: int, description: str = None, 
                      is_public: bool = True, allow_multiple_votes: bool = True, 
                      max_votes_per_user: int = 1000):
        try:
            session = VotingSession(
                title=title,
                master_id=master_id,
                description=description,
                is_public=is_public,
                allow_multiple_votes=allow_multiple_votes,
                max_votes_per_user=max_votes_per_user,
                anime_list=[]
            )
            db.add(session)
            db.commit()
            db.refresh(session)
            return session
        except Exception as e:
            print(f"错误：{e}")
            db.rollback()
            return None
    
    @staticmethod
    def add_anime_to_session(db: Session, session_id: int, anime_data: dict):
        try:
            session = db.query(VotingSession).filter(VotingSession.id == session_id).first()
            if not session:
                return {"error": "投票会话不存在"}
            
            # 仅提取并验证 bangumi_id
            bangumi_id = anime_data.get("bangumi_id")
            if not bangumi_id:
                return {"error": "缺少 bangumi_id"}
            
            # 检查是否已存在相同Bangumi ID的动漫
            # 现在anime_list中仅存储ID，简化检查逻辑
            for existing in session.anime_list:
                if existing == bangumi_id:
                    return {"error": "该动漫已在会话中存在"}
           # 仅将bangumi_id添加到列表（不存储完整信息）
            session.anime_list = session.anime_list + [bangumi_id]
            db.commit()
            db.refresh(session)
            return session
        except Exception as e:
            print(f"错误：{e}")
            db.rollback()
            return None
        
    @staticmethod
    def get_session_by_id(db: Session, session_id: int):
        return db.query(VotingSession).filter(VotingSession.id == session_id).first()

class VoteCRUD:
    """投票相关操作"""
    
    @staticmethod
    def cast_vote(db: Session, session_id: int, user_id: int, voted_anime: list):
        try:
            # 检查会话是否存在
            session = db.query(VotingSession).filter(VotingSession.id == session_id).first()
            if not session:
                return {"error": "投票会话不存在"}
            
            # 检查投票数量限制
            if not session.allow_multiple_votes and len(voted_anime) > 1:
                return {"error": "此会话不允许多选"}
            
            if len(voted_anime) > session.max_votes_per_user:
                return {"error": f"最多只能投{session.max_votes_per_user}票"}
            
            # 验证投票数据格式
            for vote in voted_anime:
                if "anime_id" not in vote or "vote_level" not in vote:
                    return {"error": "投票数据格式错误"}
                if vote["vote_level"] not in VOTE_LEVELS:
                    return {"error": "无效的投票等级"}
            
            # 检查是否已投过票
            existing_vote = db.query(Vote).filter(
                Vote.session_id == session_id,
                Vote.user_id == user_id
            ).first()
            
            if existing_vote:
                # 修改现有投票
                existing_vote.voted_anime = voted_anime
                existing_vote.voted_at = datetime.now(timezone.utc)
                db.commit()
                return existing_vote
            else:
                # 创建新投票
                vote = Vote(
                    session_id=session_id,
                    user_id=user_id,
                    voted_anime=voted_anime
                )
                db.add(vote)
                db.commit()
                db.refresh(vote)
                return vote
                
        except Exception as e:
            print(f"错误：{e}")
            db.rollback()
            return {"error": "投票失败"}
    @staticmethod
    def get_session_votes(db:Session,session_id:int):
        try:
            # 检查会话是否存在
            votes = db.query(Vote).filter(Vote.session_id == session_id).all()
            if not votes:
                return {"error": "投票不存在"}
            return votes
        except Exception as e:
            print(f"错误：{e}")
            db.rollback()
            return {"error": "获取投票失败"}
    @staticmethod
    def calculate_session_stats(db: Session, session_id: int):
        """计算投票会话的详细统计"""
        try:
            session = db.query(VotingSession).filter(VotingSession.id == session_id).first()
            if not session:
                return {"error": "投票会话不存在"}
            
            votes = VoteCRUD.get_session_votes(db, session_id)
            
            stats = {
                "total_voters": len(votes),
                "anime_stats": {},
                "overall_stats": {
                    "total_votes": 0,
                    "average_score": 0,
                    "vote_distribution": {level: 0 for level in VOTE_LEVELS}
                }
            }
            
            # 统计计算逻辑
            for vote in votes:
                for anime_vote in vote.voted_anime:
                    bangumi_id = anime_vote["anime_id"]
                    vote_level = anime_vote["vote_level"]
                    score = VOTE_LEVELS[vote_level]["score"]
                    
                    if bangumi_id not in stats["anime_stats"]:
                        stats["anime_stats"][bangumi_id] = {
                            "total_votes": 0,
                            "total_score": 0,
                            "vote_distribution": {level: 0 for level in VOTE_LEVELS},
                            "average_score": 0
                        }
                    
                    stats["anime_stats"][bangumi_id]["total_votes"] += 1
                    stats["anime_stats"][bangumi_id]["total_score"] += score
                    stats["anime_stats"][bangumi_id]["vote_distribution"][vote_level] += 1
                    
                    stats["overall_stats"]["total_votes"] += 1
                    stats["overall_stats"]["vote_distribution"][vote_level] += 1
            
            # 计算平均分
            for bangumi_id in stats["anime_stats"]:
                anime_stat = stats["anime_stats"][bangumi_id]
                if anime_stat["total_votes"] > 0:
                    anime_stat["average_score"] = round(
                        anime_stat["total_score"] / anime_stat["total_votes"], 2
                    )
            
            return stats
            
        except Exception as e:
            print(f"错误：{e}")
            return {"error": "统计计算失败"}

#get_db() 函数
#     ↓ (生产)
#Session 对象
#     ↓ (传递给)
#CRUD 方法的 db: Session 参数
#    ↓ (使用)
#数据库操作 (add, commit, query等)
#     ↓ (返回结果)
#业务逻辑处理

#get_db()函数专门用来管理session
#CRUD使用get_db()创建的seesion进行业务逻辑操作