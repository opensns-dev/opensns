# OpenZet: Open-Source AI Marketing Agent Architecture

OpenZet은 사용자의 제품 URL 하나로 시장 분석, 광고 전략 수립, 그리고 고퀄리티 광고 크리에이티브 생성을 자동화하는 에이전트 기반 마케팅 플랫폼입니다.

## 1. 시스템 개요 (System Overview)

OpenZet은 고성능 비동기 처리를 위한 **FastAPI** 백엔드와 세련된 유저 경험을 제공하는 **Next.js** 프론트엔드로 구성됩니다. 특히 AI 모델 호출부의 추상화를 통해 **Cloud API 모드**와 **Local Hosting 모드**를 모두 지원하는 하이브리드 아키텍처를 채택합니다.

## 2. 기술 스택 (Technical Stack)

| 구분 | 기술 | 비고 |
| :--- | :--- | :--- |
| **Frontend** | Next.js 15, shadcn/ui, TailwindCSS | 사용자 대시보드 및 실시간 에이전트 로그 |
| **Backend Core** | FastAPI (Python 3.11+), SQLModel | 비동기 API 및 DB 관리 |
| **Orchestration** | LangGraph, CrewAI | 상태 중심 순환형 에이전트 워크플로우 |
| **Database** | PostgreSQL, Redis | 캠페인 상태 및 작업 큐 관리 |
| **AI Engines** | OpenAI/Fal.ai (Cloud), Ollama/ComfyUI (Local) | 플러그형 엔진 어댑터 레이어 |

---

## 3. 핵심 워크플로우 (The Deep Pipeline)

OpenZet은 단순히 결과를 출력하는 것이 아니라, 에이전트 간의 협업과 검증 루프를 통해 상업적 품질을 보장합니다.

1.  **Context Mining:** `Firecrawl`을 통해 제품 상세 페이지 분석 및 경쟁사 트렌드 리서치.
2.  **Strategic Planning:** 타겟 페르소나 정의 및 3가지 이상의 마케팅 '각도(Angle)' 도출.
3.  **Creative Forge:** 
    *   **Text:** 매체별(GFA, SNS 등) 맞춤 카피 생성.
    *   **Visual:** `SAM` + `ControlNet`을 활용하여 제품 정체성을 보존한 배경 합성 이미지 생성.
4.  **Agentic Verification:** 브랜드 가이드라인 준수 여부 및 시각적 오류를 AI가 스스로 검토.
5.  **Multi-Platform Optimization:** 매체 규격별 자동 리사이징 및 예상 성과(CTR) 예측.

---

## 4. 상세 설계: 플러그형 서비스 아키텍처

사용자가 엔진에 종속되지 않고 자유롭게 어댑터를 교체할 수 있도록 설계되었습니다.

### 4.1 핵심 인터페이스 (Core Interfaces)

```python
# app/core/interfaces.py
from abc import ABC, abstractmethod

class BaseLLMAdapter(ABC):
    @abstractmethod
    async def generate_text(self, prompt: str) -> str: pass
    @abstractmethod
    async def generate_structured(self, prompt: str, schema: type) -> Any: pass

class BaseImageAdapter(ABC):
    @abstractmethod
    async def generate_ad_image(self, product_image: bytes, creative: AdCreative) -> GenerationResult: pass
```

### 4.2 엔진 레지스트리 (Engine Registry)

모든 어댑터는 중앙 레지스트리에 등록되어 런타임에 동적으로 로드됩니다.

```python
# app/core/registry.py
class EngineRegistry:
    def register_image_engine(self, name: str, adapter_cls: Type[BaseImageAdapter]):
        self._image_engines[name] = adapter_cls

    def get_image_engine(self, name: str) -> BaseImageAdapter:
        return self._image_engines[name]()
```

---

## 5. 인프라 시나리오 (Infrastructure Scenarios)

### 시나리오 A: Cloud API (SaaS형)
*   **Target:** 빠른 배포가 필요한 개인 개발자/스타트업.
*   **Stack:** GPT-4o (LLM), Fal.ai Flux.1 (Image), Jina AI (Research).

### 시나리오 B: Local Hosting (보안/절약형)
*   **Target:** 데이터 보안이 중요한 기업, GPU 보유자.
*   **Stack:** Ollama Llama 3.1 (LLM), ComfyUI API (Image), Local Crawler (Research).

---

## 6. 데이터베이스 스키마 (Main Entities)

*   **Campaigns:** 캠페인 기본 정보 및 진행 상태 (`PENDING`, `RESEARCHING`, `GENERATING`, `COMPLETED`).
*   **Agents:** 개별 에이전트의 작업 로그 및 페르소나 설정.
*   **Assets:** 생성된 광고 카피(텍스트) 및 광고 소재(이미지 URL/메타데이터).
*   **Feedback:** 에이전트 검증 결과 및 유저 수정 사항.

---

## 7. 향후 확장 계획 (Roadmap)

*   [ ] **Phase 1:** Next.js + FastAPI + Ollama/OpenAI 기본 파이프라인 구축.
*   [ ] **Phase 2:** ComfyUI API 연동을 통한 제품 보존형 비주얼 엔진 고도화.
*   [ ] **Phase 3:** LangGraph 기반의 다중 에이전트 검증 및 피드백 루프 구현.
*   [ ] **Phase 4:** 동영상 광고 소재(Short-form) 생성 모듈 추가.

---

**Sisyphus's Note:** 
본 설계는 기술적 유연성을 극대화하여 오픈소스 커뮤니티가 각자의 환경에 맞게 마케팅 에이전트를 진화시킬 수 있는 기반을 제공합니다. 특히 서비스 레이어의 격리를 통해 비즈니스 로직과 실행 엔진 간의 결합도를 최소화했습니다.
