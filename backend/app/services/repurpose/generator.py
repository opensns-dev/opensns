import json
import logging
from typing import Any

from app.core.interfaces import BaseLLMAdapter
from app.models.models import ContentPlatform, ToneStyle

logger = logging.getLogger(__name__)

TONE_INSTRUCTIONS = {
    ToneStyle.FORMAL: "존댓말을 사용하고 전문적이고 격식있는 어조로 작성하세요. 학술적이거나 비즈니스 문서 같은 톤입니다.",
    ToneStyle.CASUAL: "반말을 사용하고 캐주얼하고 편한 어조로 작성하세요. 친구에게 말하듯 자연스럽게 작성합니다.",
    ToneStyle.FRIENDLY: "존댓말을 사용하되 친근하고 따뜻한 어조로 작성하세요. 독자와 가까운 느낌을 주세요.",
}


class ContentGenerator:
    def __init__(self, llm: BaseLLMAdapter):
        self.llm = llm

    async def generate_all(
        self,
        transcript: str,
        summary: str,
        key_points: list[str],
        tone: ToneStyle,
        platforms: list[ContentPlatform],
        transcript_segments: list[dict] | None = None,
    ) -> list[dict]:
        results = []
        platform_handlers = {
            ContentPlatform.NAVER_BLOG: self._generate_naver_blog,
            ContentPlatform.X_THREAD: self._generate_x_thread,
            ContentPlatform.INSTAGRAM: self._generate_instagram,
            ContentPlatform.BRUNCH: self._generate_brunch,
            ContentPlatform.NAVER_POST: self._generate_naver_post,
            ContentPlatform.SHORT_CLIP: self._generate_short_clips,
        }

        for platform in platforms:
            handler = platform_handlers.get(platform)
            if not handler:
                continue
            try:
                if platform == ContentPlatform.SHORT_CLIP:
                    result = await handler(
                        transcript, summary, key_points, tone, transcript_segments
                    )
                else:
                    result = await handler(transcript, summary, key_points, tone)
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to generate {platform.value}: {e}")
                results.append(
                    {
                        "platform": platform.value,
                        "content": f"생성 실패: {e}",
                        "metadata": {"error": str(e)},
                    }
                )

        return results

    async def generate_summary_and_key_points(
        self, transcript: str
    ) -> tuple[str, list[str]]:
        prompt = f"""다음 영상 스크립트를 분석하세요.

스크립트:
{transcript[:8000]}

다음 JSON 형식으로 응답하세요:
{{
    "summary": "3-5문장으로 된 핵심 요약",
    "key_points": ["핵심 포인트 1", "핵심 포인트 2", "핵심 포인트 3", "핵심 포인트 4", "핵심 포인트 5"]
}}

반드시 JSON만 응답하세요."""

        response = await self.llm.generate_text(prompt)
        parsed = _parse_json_response(response)
        summary = parsed.get("summary", "")
        key_points = parsed.get("key_points", [])
        return summary, key_points

    async def _generate_naver_blog(
        self, transcript: str, summary: str, key_points: list[str], tone: ToneStyle
    ) -> dict:
        tone_instruction = TONE_INSTRUCTIONS[tone]
        prompt = f"""당신은 네이버 블로그 SEO 전문가입니다.

다음 영상 스크립트를 네이버 블로그 포스트로 변환하세요.

[톤앤매너]
{tone_instruction}

[요약]
{summary}

[핵심 포인트]
{chr(10).join(f"- {p}" for p in key_points)}

[스크립트]
{transcript[:6000]}

[네이버 블로그 SEO 규칙]
- 제목: 핵심 키워드를 앞부분에 배치, 30자 이내
- 본문: 2000-3000자
- 소제목(##)을 3-5개 사용하여 구조화
- 각 소제목 아래 2-3 문단
- [이미지 삽입 위치]를 적절히 표시
- 마지막에 핵심 요약 섹션 추가

다음 JSON 형식으로 응답하세요:
{{
    "title": "블로그 제목",
    "body": "마크다운 형식의 블로그 본문",
    "tags": ["태그1", "태그2", "태그3", "태그4", "태그5"]
}}

반드시 JSON만 응답하세요."""

        response = await self.llm.generate_text(prompt)
        parsed = _parse_json_response(response)
        return {
            "platform": ContentPlatform.NAVER_BLOG.value,
            "content": parsed.get("body", response),
            "metadata": {
                "title": parsed.get("title", ""),
                "tags": parsed.get("tags", []),
            },
        }

    async def _generate_x_thread(
        self, transcript: str, summary: str, key_points: list[str], tone: ToneStyle
    ) -> dict:
        tone_instruction = TONE_INSTRUCTIONS[tone]
        prompt = f"""당신은 X(트위터) 스레드 전문 작성자입니다.

다음 영상 스크립트를 X 스레드로 변환하세요.

[톤앤매너]
{tone_instruction}

[요약]
{summary}

[핵심 포인트]
{chr(10).join(f"- {p}" for p in key_points)}

[스크립트]
{transcript[:4000]}

[X 스레드 규칙]
- 5-7개의 트윗으로 구성
- 첫 트윗: 호기심을 자극하는 훅 (이모지 활용)
- 각 트윗 280자(한글 기준 140자) 이내
- 마지막 트윗: 요약 + CTA
- 스레드 번호 표시 (1/, 2/, ...)

다음 JSON 형식으로 응답하세요:
{{
    "tweets": ["1/ 첫번째 트윗", "2/ 두번째 트윗", ...]
}}

반드시 JSON만 응답하세요."""

        response = await self.llm.generate_text(prompt)
        parsed = _parse_json_response(response)
        tweets = parsed.get("tweets", [])
        return {
            "platform": ContentPlatform.X_THREAD.value,
            "content": "\n\n---\n\n".join(tweets),
            "metadata": {"tweet_count": len(tweets)},
        }

    async def _generate_instagram(
        self, transcript: str, summary: str, key_points: list[str], tone: ToneStyle
    ) -> dict:
        tone_instruction = TONE_INSTRUCTIONS[tone]
        prompt = f"""당신은 인스타그램 콘텐츠 전문가입니다.

다음 영상 스크립트를 인스타그램 캡션으로 변환하세요.

[톤앤매너]
{tone_instruction}

[요약]
{summary}

[핵심 포인트]
{chr(10).join(f"- {p}" for p in key_points)}

[스크립트]
{transcript[:4000]}

[인스타그램 규칙]
- 캡션: 핵심 메시지를 첫 줄에, 전체 500-1000자
- 이모지 적절히 사용
- 줄바꿈으로 가독성 확보
- 해시태그: 인기 태그 10개 + 니치 태그 10개 = 총 20개

다음 JSON 형식으로 응답하세요:
{{
    "caption": "인스타그램 캡션 텍스트",
    "hashtags": ["해시태그1", "해시태그2", ...]
}}

반드시 JSON만 응답하세요."""

        response = await self.llm.generate_text(prompt)
        parsed = _parse_json_response(response)
        hashtags = parsed.get("hashtags", [])
        caption = parsed.get("caption", response)
        hashtag_text = " ".join(f"#{tag.lstrip('#')}" for tag in hashtags)
        full_content = f"{caption}\n\n{hashtag_text}"
        return {
            "platform": ContentPlatform.INSTAGRAM.value,
            "content": full_content,
            "metadata": {"hashtags": hashtags},
        }

    async def _generate_brunch(
        self, transcript: str, summary: str, key_points: list[str], tone: ToneStyle
    ) -> dict:
        tone_instruction = TONE_INSTRUCTIONS[tone]
        prompt = f"""당신은 브런치 스토리 전문 작가입니다.

다음 영상 스크립트를 브런치 에세이로 변환하세요.

[톤앤매너]
{tone_instruction}

[요약]
{summary}

[핵심 포인트]
{chr(10).join(f"- {p}" for p in key_points)}

[스크립트]
{transcript[:6000]}

[브런치 스토리 규칙]
- 에세이/스토리텔링 형식
- 서브타이틀 포함
- 문학적이고 감성적인 표현 사용
- 독자의 공감을 이끄는 개인적 시각
- 1500-2500자
- 과도한 서식 지양, 자연스러운 흐름

다음 JSON 형식으로 응답하세요:
{{
    "title": "에세이 제목",
    "subtitle": "서브타이틀",
    "body": "에세이 본문"
}}

반드시 JSON만 응답하세요."""

        response = await self.llm.generate_text(prompt)
        parsed = _parse_json_response(response)
        title = parsed.get("title", "")
        subtitle = parsed.get("subtitle", "")
        body = parsed.get("body", response)
        full_content = f"# {title}\n\n*{subtitle}*\n\n{body}" if title else body
        return {
            "platform": ContentPlatform.BRUNCH.value,
            "content": full_content,
            "metadata": {
                "title": title,
                "subtitle": subtitle,
            },
        }

    async def _generate_naver_post(
        self, transcript: str, summary: str, key_points: list[str], tone: ToneStyle
    ) -> dict:
        tone_instruction = TONE_INSTRUCTIONS[tone]
        prompt = f"""당신은 네이버 포스트 카드형 콘텐츠 전문가입니다.

다음 영상 스크립트를 네이버 포스트 카드형 콘텐츠로 변환하세요.

[톤앤매너]
{tone_instruction}

[요약]
{summary}

[핵심 포인트]
{chr(10).join(f"- {p}" for p in key_points)}

[스크립트]
{transcript[:5000]}

[네이버 포스트 규칙]
- 4-6장의 카드로 구성
- 각 카드: 제목(짧고 임팩트있게) + 본문(200-400자)
- 비주얼 중심, 핵심만 전달
- 각 카드에 이미지 제안 포함

다음 JSON 형식으로 응답하세요:
{{
    "title": "포스트 제목",
    "cards": [
        {{"card_title": "카드 제목", "body": "카드 본문", "image_suggestion": "이미지 설명"}},
        ...
    ]
}}

반드시 JSON만 응답하세요."""

        response = await self.llm.generate_text(prompt)
        parsed = _parse_json_response(response)
        title = parsed.get("title", "")
        cards = parsed.get("cards", [])
        card_texts = []
        for i, card in enumerate(cards, 1):
            card_title = card.get("card_title", f"카드 {i}")
            body = card.get("body", "")
            card_texts.append(f"### [{i}] {card_title}\n\n{body}")
        full_content = f"# {title}\n\n" + "\n\n---\n\n".join(card_texts)
        return {
            "platform": ContentPlatform.NAVER_POST.value,
            "content": full_content,
            "metadata": {
                "title": title,
                "card_count": len(cards),
                "cards": cards,
            },
        }

    async def _generate_short_clips(
        self,
        transcript: str,
        summary: str,
        key_points: list[str],
        tone: ToneStyle,
        transcript_segments: list[dict] | None = None,
    ) -> dict:
        segments_context = ""
        if transcript_segments:
            sample = transcript_segments[:100]
            segments_context = "\n[타임스탬프 세그먼트]\n"
            for seg in sample:
                start = _format_timestamp(seg["start"])
                end = _format_timestamp(seg["end"])
                segments_context += f"[{start}-{end}] {seg['text']}\n"

        prompt = f"""당신은 숏폼 콘텐츠 전문가입니다.

다음 영상 스크립트에서 숏폼 클립(릴스, 쇼츠)으로 만들기 좋은 구간을 추천하세요.

[요약]
{summary}

[핵심 포인트]
{chr(10).join(f"- {p}" for p in key_points)}

[스크립트]
{transcript[:5000]}
{segments_context}

[추천 기준]
- 3-5개 클립 구간 추천
- 각 클립 15-60초
- 후킹 포인트가 강한 구간
- 단독으로 이해 가능한 자기완결적 내용
- start_seconds/end_seconds는 대략적 타임스탬프

다음 JSON 형식으로 응답하세요:
{{
    "clips": [
        {{
            "title": "클립 제목",
            "start_seconds": 0,
            "end_seconds": 45,
            "reason": "추천 이유",
            "hook": "이 클립의 후킹 첫 문장"
        }},
        ...
    ]
}}

반드시 JSON만 응답하세요."""

        response = await self.llm.generate_text(prompt)
        parsed = _parse_json_response(response)
        clips = parsed.get("clips", [])
        clip_texts = []
        for i, clip in enumerate(clips, 1):
            start = _format_timestamp(clip.get("start_seconds", 0))
            end = _format_timestamp(clip.get("end_seconds", 0))
            clip_texts.append(
                f"### 클립 {i}: {clip.get('title', '')}\n"
                f"⏱️ {start} ~ {end}\n"
                f"🎯 {clip.get('reason', '')}\n"
                f'🪝 "{clip.get("hook", "")}"'
            )
        full_content = "\n\n---\n\n".join(clip_texts)
        return {
            "platform": ContentPlatform.SHORT_CLIP.value,
            "content": full_content,
            "metadata": {"clips": clips, "clip_count": len(clips)},
        }


def _format_timestamp(seconds: float | int) -> str:
    seconds = int(seconds)
    minutes, secs = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"


def _parse_json_response(response: str) -> dict:
    response = response.strip()
    if response.startswith("```json"):
        response = response[7:]
    if response.startswith("```"):
        response = response[3:]
    if response.endswith("```"):
        response = response[:-3]
    response = response.strip()

    try:
        return json.loads(response)
    except json.JSONDecodeError:
        start = response.find("{")
        end = response.rfind("}") + 1
        if start >= 0 and end > start:
            try:
                return json.loads(response[start:end])
            except json.JSONDecodeError:
                pass
        logger.warning("Failed to parse LLM JSON response")
        return {}
