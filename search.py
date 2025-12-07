from fastapi import APIRouter, Query
import aiohttp
from typing import List, Dict,Any

router = APIRouter(prefix="/search", tags=["动漫搜索"])

@router.get("/anime", response_model=Dict[str, Any])
async def search_anime(
    keyword: str = Query(..., description="搜索关键词（动漫名称）"),
    limit: int = Query(10, ge=1, le=50, description="返回结果数量限制")
):
    """
    通过关键词搜索动漫(调用Bangumi API)
    用于帮助管理者查找动漫对应的bangumi_id
    """
    url = "https://api.bgm.tv/v0/search/subjects"
    
    # 请求参数：搜索关键词、类型为2（动画）、返回数量
    payload = {
        "keyword": keyword,
        "type": 2,  # 2表示动画类型
        "limit": limit
    }
    
    # 请求头，模拟合法客户端
    headers = {
        "User-Agent": "anime_voting/1.0",
        "Content-Type": "application/json"
    }
    
    try:
        # 异步请求Bangumi搜索API
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers) as response:
                if response.status != 200:
                    return {"error": f"搜索失败，状态码: {response.status}", "keyword": keyword}
                
                result = await response.json()
                raw_data = result.get("data", [])
                
                # 二次筛选：确保只返回类型为2（动画）的结果
                # 因为Bangumi API的type参数是"或"关系，可能返回其他类型
                anime_list = [
                    {
                        "bangumi_id": item.get("id"),
                        "title": item.get("name"),
                        "title_cn": item.get("name_cn"),
                        "image": item.get("images", {}).get("large"),
                        "score": item.get("score"),
                        "type": item.get("type")
                    }
                    for item in raw_data
                    if item.get("type") == 2  # 严格筛选动画类型
                ]
                
                return {
                    "keyword": keyword,
                    "count": len(anime_list),
                    "results": anime_list
                }
                
    except Exception as e:
        return {"error": f"搜索过程出错: {str(e)}", "keyword": keyword}