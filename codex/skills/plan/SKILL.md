---
name: plan
description: 비트리비얼한 작업의 구조화된 구현 계획 생성. 사용자가 "계획 세워줘", "plan", "$plan" 등 계획 수립을 요청하거나, 3+ 스텝/아키텍처 결정/멀티스텝 검증이 필요한 작업일 때 사용한다. 코드 수정 없이 계획서만 생성한다.
---

# Plan — Structured Implementation Plan

작업의 구현 계획을 표준 포맷으로 생성한다.

## Rules

1. **Read-only**: 계획 작성만 수행한다. 코드를 수정하지 않는다. 필요한 파일은 읽기로만 조회한다.
2. **승인 전 실행 금지**: 사용자의 명시적 승인 전에는 어떤 변경도 시작하지 않는다.
3. **Evidence-based**: 계획의 근거가 되는 파일·라인을 명시한다.
4. **Scope discipline**: 요청된 범위 밖 리팩토링·포매팅·개선을 계획에 섞지 않는다.

## Workflow

1. **요구 재진술**: 사용자가 원하는 것을 한 문장으로 요약한다.
2. **탐색**: 관련 코드를 파악한다. 재사용 가능한 기존 함수·유틸·패턴을 먼저 찾는다.
3. **초안 작성**: 아래 Output Format에 따라 계획서를 작성한다.
4. **미결 질문**: 확신이 없거나 선택지가 있는 항목은 별도 섹션에 명시한다.
5. **사용자 확인 대기**: 계획 출력 후 승인·수정 요청을 기다린다.

## Output Format

```markdown
# Plan: {제목}

## Context
{왜 이 작업이 필요한가. 어떤 문제·요구사항이 trigger인가. 기대 결과.}

## Goals / Non-goals
**Goals**
- {달성할 것}

**Non-goals**
- {의도적으로 하지 않을 것 — 범위 규율}

## Change Scope
- `{파일 또는 모듈}` — {어떤 변경}

## Step Plan (checklist)
- [ ] Step 1: {구체 행동}
- [ ] Step 2: {구체 행동}
- [ ] Step 3: {구체 행동}

## Verification Plan
- **Unit**: {테스트 파일 또는 명령}
- **Integration**: {통합 시나리오}
- **Manual**: {수동 확인 절차}

## Risks / Rollback
- **Risk**: {리스크} → **Mitigation**: {완화책}
- **Rollback**: {롤백 방법}

## Evidence (참조)
- `{파일:라인}` — {왜 참조했는지}

## 미결 질문 (optional)
1. {질문} — 사용자 확인 필요
```

## 주의

- **Scope Discipline** — 계획에 범위 외 리팩토링·포매팅을 섞지 않는다.
- 요구사항이 모호하면 Investigation 결과·가설·초안을 먼저 제시하고 **최소 질문**을 병행한다.
- 파괴적·prod 영향 작업은 Target + Exact action + Risk acceptance 3요소를 계획서에 명시한다.
