from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from database import get_db, User,SessionCreate,AddAnime,CastVote
from dependencies import get_current_user,require_ownership
from crud import VotingSessionCRUD, VoteCRUD
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/api/voting", tags=["投票功能"])

@router.post("/sessions")
async def create_voting_session(
    # title: str,
    # description: Optional[str] = None,
    # is_public: bool = True,
    # allow_multiple_votes: bool = True,
    # max_votes_per_user: int = 1000,
    sessiondata:SessionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建投票会话（需要登录）"""
    session = VotingSessionCRUD.create_session(
        db=db,
        title=sessiondata.title,
        master_id=current_user.id,
        description=sessiondata.description,
        is_public=sessiondata.is_public,
        allow_multiple_votes=sessiondata.allow_multiple_votes,
        max_votes_per_user=sessiondata.max_votes_per_user
    )
    
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="创建会话失败"
        )
    
    return {
        "message": "投票会话创建成功",
        "session_id": session.id,
        "title": session.title,
        "created_by": current_user.username
    }

@router.post("/sessions/{session_id}/anime")
async def add_anime_to_session(
    data:AddAnime,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """向投票会话添加动漫（需要登录）"""
    # 首先检查会话是否存在且用户有权操作
    from database import VotingSession
    session = db.query(VotingSession).filter(VotingSession.id == data.session_id).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="投票会话不存在"
        )
    
    # 检查权限：只有会话创建者或管理员可以添加动漫
    if session.master_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权向此会话添加动漫"
        )
    
     
    # 传递仅包含 bangumi_id 的数据
    result = VotingSessionCRUD.add_anime_to_session(
        db, 
        data.session_id, 
        {"bangumi_id": data.bangumi_id}
    )
    
    if result is None or (isinstance(result, dict) and "error" in result):
        error_msg = result.get("error", "添加动漫失败") if isinstance(result, dict) else "添加动漫失败"
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )
    
    return {
        "message": "动漫添加成功",
        "session_id": data.session_id,
        "bangumi_id": data.bangumi_id
    }

@router.get("/sessions/public")
async def get_voting_sessions(
    public_only: bool = True,
    db: Session = Depends(get_db)
):
    """获取投票会话列表（公开访问）"""
    from database import VotingSession
    
    query = db.query(VotingSession)
    
    if public_only:
        query = query.filter(VotingSession.is_public == True)
    
    sessions = query.all()
    
    return {
        "sessions": [
            {
                "id": session.id,
                "title": session.title,
                "description": session.description,
                "is_public": session.is_public,
                "anime_count": len(session.anime_list) if session.anime_list else 0,
                "created_at": session.created_at.isoformat() if session.created_at else None
            }
            for session in sessions
        ]
    }

@router.get("/sessions/{session_id}")
async def get_session_detail(
    session_id: int,
    db: Session = Depends(get_db)
):
    """获取投票会话详情（公开访问）"""
    from database import VotingSession
    
    session = db.query(VotingSession).filter(VotingSession.id == session_id).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="投票会话不存在"
        )
    
    if not session.is_public:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="此会话不公开"
        )
    
    return {
        "session": {
            "id": session.id,
            "title": session.title,
            "description": session.description,
            "is_public": session.is_public,
            "allow_multiple_votes": session.allow_multiple_votes,
            "max_votes_per_user": session.max_votes_per_user,
            "bangumi_ids": session.anime_list or [],  # 明确返回的是ID列表
            "created_at": session.created_at.isoformat() if session.created_at else None
        }
    }

@router.post("/sessions/{session_id}/vote")
async def cast_vote(
    data:CastVote,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """进行投票（需要登录）"""
    result = VoteCRUD.cast_vote(
        db=db,
        session_id=data.session_id,
        user_id=current_user.id,
        voted_anime=data.voted_anime
    )
    
    if result is None:
                return JSONResponse(
                    content={"error": "账号或密码错误"}, 
                    status_code=400
                )
        
    
    return {
        "message": "投票成功",
        "vote_id": result.id if hasattr(result, 'id') else None,
        # hasattr(result, 'id') 检查 result 对象是否有名为 'id' 的属性。
        "voted_anime_count": len(data.voted_anime)
    }

@router.get("/sessions/{session_id}/results")
async def get_voting_results(
    session_id: int,
    db: Session = Depends(get_db)
):
    """获取投票结果（公开访问）"""
    stats = VoteCRUD.calculate_session_stats(db, session_id)
    
    if "error" in stats:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=stats["error"]
        )
    
    return {
        "session_id": session_id,
        "stats": stats
    }

@router.get("/my-sessions")
async def get_my_sessions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取当前用户创建的投票会话（需要登录）"""
    from database import VotingSession
    
    sessions = db.query(VotingSession).filter(
        VotingSession.master_id == current_user.id
    ).all()
    
    return {
        "sessions": [
            {
                "id": session.id,
                "title": session.title,
                "description": session.description,
                "is_public": session.is_public,
                "anime_count": len(session.anime_list) if session.anime_list else 0,
                "total_votes": len(session.votes) if hasattr(session, 'votes') else 0,
                "created_at": session.created_at.isoformat() if session.created_at else None
            }
            for session in sessions
        ]
    }