---
name: task-complete
description: 작업 완료 시 Linear 리뷰중 + Notion 기록
triggers:
  - PostToolUse
matcher:
  - Edit
  - Write
---

# Task Complete Hook

코드 편집/작성 완료 후 자동 실행되는 훅.

## 자동 실행 작업

1. **변경 사항 요약**
   - 수정된 파일 목록 수집
   - 변경 내용 한 줄 요약 생성

2. **Linear 티켓 업데이트**
   - 현재 진행중 티켓을 "In Review" 상태로 변경
   - 코멘트 추가: 변경 사항 요약 + 수정 파일 목록

3. **Notion 활동 로그**
   - Notion "📝 회의록" DB에 작업 로그 추가 (선택적)
   - 큰 변경(파일 3개 이상)일 때만 회의록 페이지 생성

4. **다음 단계 안내**
   - 코드면 → qa 에이전트 호출 제안
   - 보안 관련 파일이면 → security 에이전트 호출 제안

## 활동 로그
- "✅ 작업 완료: [티켓ID] → 리뷰중"