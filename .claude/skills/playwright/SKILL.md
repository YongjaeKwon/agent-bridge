\---

name: playwright-automation

description: Playwright로 네이버 블로그 자동화. 로그인, 글쓰기, 이미지 업로드 패턴

\---



\## When to Use

\- 네이버 블로그 자동화 작업

\- 브라우저 자동화 필요할 때

\- 스크린샷 캡처 필요할 때



\## Rules

\- headless=False로 디버깅, 완성 후 headless=True

\- 실패 시 반드시 스크린샷 저장

\- 로그인 세션 재사용으로 속도 최적화

\- NAVER\_ID, NAVER\_PW는 .env에서만 읽기



\## Patterns



\### 기본 자동화 구조

```python

from playwright.async\_api import async\_playwright

import os



async def naver\_post(title: str, content: str):

&#x20;   async with async\_playwright() as p:

&#x20;       browser = await p.chromium.launch(headless=False)

&#x20;       context = await browser.new\_context()

&#x20;       page = await context.new\_page()

&#x20;       

&#x20;       try:

&#x20;           await page.goto("https://nid.naver.com/nidlogin.login")

&#x20;           await page.fill("#id", os.getenv("NAVER\_ID"))

&#x20;           await page.fill("#pw", os.getenv("NAVER\_PW"))

&#x20;           await page.click(".btn\_login")

&#x20;           await page.wait\_for\_load\_state("networkidle")

&#x20;           # 포스팅 로직

&#x20;       except Exception as e:

&#x20;           await page.screenshot(path=f"error\_{title}.png")

&#x20;           raise e

&#x20;       finally:

&#x20;           await browser.close()

```

