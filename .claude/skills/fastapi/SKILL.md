\---

name: fastapi-patterns

description: FastAPI 개발 패턴. 라우터 구조, 의존성 주입, Pydantic 모델, 에러 핸들링

\---



\## When to Use

\- FastAPI 엔드포인트 만들 때

\- API 응답 모델 정의할 때

\- 미들웨어 설정할 때



\## Patterns



\### 라우터 구조

```python

from fastapi import APIRouter, HTTPException

from pydantic import BaseModel



router = APIRouter(prefix="/blog", tags=\["blog"])



class PostRequest(BaseModel):

&#x20;   title: str

&#x20;   content: str

&#x20;   platforms: list\[str]



@router.post("/post")

async def create\_post(request: PostRequest):

&#x20;   try:

&#x20;       results = {}

&#x20;       for platform in request.platforms:

&#x20;           results\[platform] = await post\_to\_platform(platform, request)

&#x20;       return {"success": True, "results": results}

&#x20;   except Exception as e:

&#x20;       raise HTTPException(status\_code=500, detail=str(e))

```

