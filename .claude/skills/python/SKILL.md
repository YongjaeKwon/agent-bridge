\---

name: python-patterns

description: Python 개발 패턴 및 베스트 프랙티스. PEP8, async/await, 타입 힌트, pytest 활용

\---



\## When to Use

\- Python 코드 작성할 때

\- FastAPI 엔드포인트 구현할 때

\- 비동기 처리 필요할 때



\## Rules

\- PEP8 준수

\- 타입 힌트 필수

\- async/await 우선 사용

\- .env에서만 환경변수 읽기

\- 예외처리 try/except 필수



\## Patterns



\### 기본 클래스 구조

```python

from abc import ABC, abstractmethod

from typing import Optional



class BasePlatform(ABC):

&#x20;   def \_\_init\_\_(self, api\_key: str):

&#x20;       self.api\_key = api\_key

&#x20;   

&#x20;   @abstractmethod

&#x20;   async def post(self, title: str, content: str) -> dict:

&#x20;       pass

```



\### 환경변수 로드

```python

from dotenv import load\_dotenv

import os



load\_dotenv()

API\_KEY = os.getenv("API\_KEY")

```

