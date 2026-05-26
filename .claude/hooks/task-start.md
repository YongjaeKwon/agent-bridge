---
name: task-start
description: 작업 시작 시 Linear 티켓 자동 진행중 처리
triggers:
  - PreToolUse
matcher:
  - Edit
  - Write
---

# Task Start Hook

코드 편집/작성 시작 전에 자동 실행되는 훅.

## 자동 실행 작업

1. **현재 작업 컨텍스트 파악**
   - 어떤 파일을 수정/작성하려는지 확인
   - 파일 경로에서 관련 플랫폼 추론 (tistory.py → Tistory)

2. **Linear 티켓 조회**
   - `mcp_linear`로 현재 활성 사이클의 티켓 검색
   - 파일명/플랫폼명으로 매칭되는 티켓 찾기

3. **티켓 상태 업데이트**
   - 매칭되는 티켓 발견 시: 상태를 "In Progress"로 변경
   - 매칭 없으면: 새 티켓 자동 생성 (제목: 수정 중인 파일명)

4. **활동 로그**
   - 콘솔에 "🎯 작업 시작: [티켓ID] [티켓명]" 출력

## 에러 처리
- Linear 호출 실패 시 작업은 계속 진행, 경고만 출력