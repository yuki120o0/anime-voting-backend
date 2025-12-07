from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any

from database import get_db, User
from dependencies import get_current_user
from crud import UserCRUD
from security import PasswordUtils

router = APIRouter(prefix="/user", tags=["用户资料"])

@router.get("/profile")
async def get_user_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取当前用户资料"""
    return {
        "id": current_user.id,
        "username": current_user.username,
        "role": current_user.role,
        "created_at": current_user.created_at.isoformat() if current_user.created_at else None
    }

@router.put("/profile")
async def update_user_profile(
    profile_data: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新用户资料"""
    try:
        # 目前只允许更新用户名，需要检查唯一性
        if 'username' in profile_data and profile_data['username'] != current_user.username:
            existing_user = UserCRUD.get_user_by_username(db, profile_data['username'])
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="用户名已存在"
                )
            current_user.username = profile_data['username']
        
        db.commit()
        db.refresh(current_user)
        
        return {"message": "资料更新成功", "user": current_user}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新资料失败: {str(e)}"
        )
@router.get("/votes")
async def get_user_votes(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取用户的投票记录"""
    from database import Vote, VotingSession
    
    votes = db.query(Vote).filter(Vote.user_id == current_user.id).all()
    
    vote_history = []
    for vote in votes:
        session = db.query(VotingSession).filter(VotingSession.id == vote.session_id).first()
        vote_history.append({
            "vote_id": vote.id,
            "session_id": vote.session_id,
            "session_title": session.title if session else "未知会话",
            "voted_anime": vote.voted_anime,
            "created_at": vote.created_at.isoformat() if vote.created_at else None
        })
    
    return {"votes": vote_history}

@router.get("/sessions")
async def get_user_sessions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取用户创建的投票会话"""
    from database import VotingSession
    
    sessions = db.query(VotingSession).filter(VotingSession.master_id == current_user.id).all()
    
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

@router.get("/stats")
async def get_user_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取用户统计信息"""
    from database import VotingSession, Vote
    
    # 用户创建的会话数量
    session_count = db.query(VotingSession).filter(VotingSession.master_id == current_user.id).count()
    
    # 用户投票次数
    vote_count = db.query(Vote).filter(Vote.user_id == current_user.id).count()
    
    # 用户参与的会话数量（去重）
    participated_sessions = db.query(Vote.session_id).filter(Vote.user_id == current_user.id).distinct().count()
    
    return {
        "created_sessions": session_count,
        "total_votes": vote_count,
        "participated_sessions": participated_sessions
    }   