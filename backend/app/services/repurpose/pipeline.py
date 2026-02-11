import json
import logging
import os
import shutil

from sqlmodel import Session

from app.db import engine
from app.models.models import (
    RepurposeJob,
    RepurposeStatus,
    RepurposeContent,
    ContentPlatform,
    User,
    UserSettings,
)
from app.core.encryption import decrypt_api_key
from app.core.config import settings as app_settings
from app.core.registry import engine_registry
from app.services.repurpose.youtube import extract_audio
from app.services.repurpose.transcribe import transcribe_audio
from app.services.repurpose.generator import ContentGenerator
from app.services.usage import use_credits
from app.models.models import CREDIT_COSTS

logger = logging.getLogger(__name__)


def _get_openai_api_key(session: Session, user_id: int) -> str | None:
    user_settings = session.get(UserSettings, user_id)
    if user_settings and user_settings.openai_api_key:
        try:
            return decrypt_api_key(
                user_settings.openai_api_key,
                app_settings.API_KEY_ENCRYPTION_KEY,
            )
        except Exception:
            pass
    return app_settings.OPENAI_API_KEY


def _get_llm_engine_name(session: Session, user_id: int) -> str:
    user_settings = session.get(UserSettings, user_id)
    if user_settings and user_settings.default_llm_engine:
        return user_settings.default_llm_engine
    return app_settings.DEFAULT_LLM_ENGINE


def _update_job_status(
    session: Session, job: RepurposeJob, status: RepurposeStatus, **kwargs: object
) -> None:
    job.status = status
    for key, value in kwargs.items():
        setattr(job, key, value)
    from app.models.models import utc_now

    job.updated_at = utc_now()
    session.add(job)
    session.commit()


async def _broadcast_progress(job_id: int, step: str, message: str) -> None:
    try:
        from app.api.websocket import repurpose_manager

        await repurpose_manager.broadcast_to_campaign(
            job_id,
            {
                "type": "repurpose_progress",
                "step": step,
                "message": message,
            },
        )
    except Exception:
        pass


async def run_repurpose_pipeline(job_id: int) -> None:
    audio_path: str | None = None
    temp_dir: str | None = None

    try:
        with Session(engine) as session:
            job = session.get(RepurposeJob, job_id)
            if not job:
                return

            youtube_url = job.youtube_url
            user_id = job.user_id
            tone_style = job.tone_style
            target_platforms_raw = json.loads(job.target_platforms)
            target_platforms = [ContentPlatform(p) for p in target_platforms_raw]

            api_key = _get_openai_api_key(session, user_id)
            llm_engine_name = _get_llm_engine_name(session, user_id)

            _update_job_status(session, job, RepurposeStatus.EXTRACTING)

        await _broadcast_progress(job_id, "extracting", "YouTube 오디오 추출 중...")

        audio_path, metadata = await extract_audio(youtube_url)
        temp_dir = os.path.dirname(audio_path)

        with Session(engine) as session:
            job = session.get(RepurposeJob, job_id)
            if not job:
                return
            _update_job_status(
                session,
                job,
                RepurposeStatus.TRANSCRIBING,
                video_title=metadata.get("title"),
                video_duration=metadata.get("duration"),
            )

        await _broadcast_progress(job_id, "transcribing", "음성을 텍스트로 변환 중...")

        if not api_key:
            raise RuntimeError(
                "OpenAI API 키가 설정되지 않았습니다. 설정에서 API 키를 입력하세요."
            )

        transcript, segments = await transcribe_audio(audio_path, api_key)

        with Session(engine) as session:
            job = session.get(RepurposeJob, job_id)
            if not job:
                return
            _update_job_status(
                session,
                job,
                RepurposeStatus.GENERATING,
                transcript=transcript,
                transcript_segments=json.dumps(segments, ensure_ascii=False),
            )

        await _broadcast_progress(job_id, "generating", "AI 콘텐츠 생성 중...")

        llm = engine_registry.get_llm_engine(llm_engine_name)
        generator = ContentGenerator(llm)

        summary, key_points = await generator.generate_summary_and_key_points(
            transcript
        )

        with Session(engine) as session:
            job = session.get(RepurposeJob, job_id)
            if not job:
                return
            job.summary = summary
            job.key_points = json.dumps(key_points, ensure_ascii=False)
            session.add(job)
            session.commit()

        results = await generator.generate_all(
            transcript=transcript,
            summary=summary,
            key_points=key_points,
            tone=tone_style,
            platforms=target_platforms,
            transcript_segments=segments,
        )

        with Session(engine) as session:
            job = session.get(RepurposeJob, job_id)
            if not job:
                return

            for result in results:
                content = RepurposeContent(
                    job_id=job_id,
                    platform=ContentPlatform(result["platform"]),
                    content=result["content"],
                    content_metadata=json.dumps(
                        result.get("metadata", {}), ensure_ascii=False
                    ),
                )
                session.add(content)

            user = session.get(User, user_id)
            if user:
                use_credits(
                    session,
                    user,
                    CREDIT_COSTS["repurpose"],
                    resource_type="repurpose",
                )

            _update_job_status(session, job, RepurposeStatus.COMPLETED)

        await _broadcast_progress(job_id, "completed", "콘텐츠 생성 완료!")

    except Exception as e:
        logger.error(f"Repurpose pipeline failed for job {job_id}: {e}")
        with Session(engine) as session:
            job = session.get(RepurposeJob, job_id)
            if job:
                _update_job_status(
                    session,
                    job,
                    RepurposeStatus.FAILED,
                    error=str(e)[:500],
                )
        await _broadcast_progress(job_id, "failed", f"실패: {e}")

    finally:
        if temp_dir and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)
