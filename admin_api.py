from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from database import get_db, User
from dependencies import require_admin, require_ownership
from crud import UserCRUD, VotingSessionCRUD

router = APIRouter(prefix="/admin", tags=["管理员API"])

@router.get("/users")
async def get_all_users(
    current_user: User = Depends(require_admin("admin")),
    db: Session = Depends(get_db)
):
    """获取所有用户列表（仅管理员）"""
    users = UserCRUD.get_all_users(db)
    
    return {
        "users": [
            {
                "id": user.id,
                "username": user.username,
                "role": user.role,
                "created_at": user.created_at.isoformat() if user.created_at else None
            }
            for user in users
        ]
    }

@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    current_user: User = Depends(require_admin("admin")),
    db: Session = Depends(get_db)
):
    """删除用户（仅管理员）"""
    user_to_delete = UserCRUD.get_user_by_id(db, user_id)
    
    if not user_to_delete:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 防止管理员删除自己
    if user_to_delete.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能删除自己的账户"
        )
    
    try:
        db.delete(user_to_delete)
        db.commit()
        return {"message": f"用户 {user_to_delete.username} 已删除"}
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除用户失败: {str(e)}"
        )

@router.put("/users/{user_id}/role")
async def update_user_role(
    user_id: int,
    new_role: str,
    current_user: User = Depends(require_admin("admin")),
    db: Session = Depends(get_db)
):
    """更新用户角色（仅管理员）"""
    if new_role not in ["admin", "user", "guest"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的角色"
        )
    
    user_to_update = UserCRUD.get_user_by_id(db, user_id)
    
    if not user_to_update:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    try:
        user_to_update.role = new_role
        db.commit()
        db.refresh(user_to_update)
        
        return {
            "message": f"用户 {user_to_update.username} 角色已更新为 {new_role}",
            "user": {
                "id": user_to_update.id,
                "username": user_to_update.username,
                "role": user_to_update.role
            }
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新用户角色失败: {str(e)}"
        )

@router.get("/sessions")
async def get_all_sessions(
    current_user: User = Depends(require_admin("admin")),
    db: Session = Depends(get_db)
):
    """获取所有投票会话（仅管理员）"""
    from database import VotingSession
    
    sessions = db.query(VotingSession).all()
    
    return {
        "sessions": [
            {
                "id": session.id,
                "title": session.title,
                "master_id": session.master_id,
                "is_public": session.is_public,
                "created_at": session.created_at.isoformat() if session.created_at else None,
                # isoformat()：Python datetime对象的方法，将时间转换为ISO 8601标准格式
                "anime_count": len(session.anime_list) if session.anime_list else 0
            }
            for session in sessions
        ]
    }