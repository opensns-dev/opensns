# VIDEO SERVICE

**Generated:** 2026-04-07

## OVERVIEW

Video generation service implementing `BaseVideoAdapter` interface for multiple engines. Supports standard video generation (image-to-video) and UGC avatar-based video generation.

## STRUCTURE

```
backend/app/services/video/
├── interfaces.py          # BaseVideoAdapter abstract class
├── fal_video.py           # Fal.ai video generation
├── runway.py              # Runway ML
├── comfyui_video.py       # ComfyUI video
├── heygen.py              # HeyGen UGC avatars
├── did.py                 # D-ID UGC avatars
├── sadtalker.py           # Self-hosted SadTalker UGC
└── fallback.py            # Fallback video adapter
```

## WHERE TO LOOK

| Task | Location | Notes |
|------|----------|-------|
| Add video engine | `interfaces.py` | Extend `BaseVideoAdapter` |
| Implement Fal.ai | `fal_video.py` | Image-to-video via Fal |
| Implement Runway | `runway.py` | Motion brush support |
| Implement ComfyUI | `comfyui_video.py` | Custom workflows |
| Add UGC engine | `heygen.py`, `did.py`, `sadtalker.py` | Implement `supports_ugc()` |
| Register engine | `core/initializers.py` | `engine_registry.register_video_engine()` |

## CONVENTIONS

### Adapter Implementation
- Inherit from `BaseVideoAdapter` in `interfaces.py`
- Implement `generate_video()` for standard generation
- Implement `image_to_video()` for motion from image
- Return `VideoGenerationResult` with `video_url` and `metadata`

### UGC Support
- Implement `supports_ugc() -> bool` to declare capability
- Implement `generate_ugc_video()` for avatar-based generation
- Implement `list_avatars()` and `list_voices()` for selection
- Return `AvatarInfo` and `VoiceInfo` lists

### Registration
- Import adapter in `core/initializers.py`
- Call `engine_registry.register_video_engine("name", AdapterClass)`
- Engine IDs: `fal-video`, `runway`, `comfyui-video`, `heygen`, `did`, `sadtalker`, `fallback`

## KEY FILES

| File | Purpose |
|------|---------|
| `interfaces.py` | `BaseVideoAdapter` abstract class, request/result models |
| `fal_video.py` | Fal.ai video generation adapter |
| `runway.py` | Runway ML video generation adapter |
| `comfyui_video.py` | ComfyUI workflow-based video adapter |
| `heygen.py` | HeyGen UGC avatar video adapter |
| `did.py` | D-ID UGC avatar video adapter |
| `sadtalker.py` | Self-hosted SadTalker UGC adapter |
| `fallback.py` | Fallback adapter for graceful degradation |

## ANTI-PATTERNS

- **NEVER** skip `supports_ugc()` check before calling UGC methods
- **NEVER** return raw API responses, always wrap in `VideoGenerationResult`
- **NEVER** hardcode engine credentials, use settings/config
- **NEVER** ignore fallback handling when primary engine fails
