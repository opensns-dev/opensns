import json
from datetime import datetime, UTC

from sqlmodel import Session, select

from app.models.models import Asset, Campaign, User, UserSettings


def apply_ai_label(
    asset: Asset, user_settings: UserSettings, session: Session
) -> Asset:
    """Apply AI disclosure label metadata to an asset based on user settings."""
    if not user_settings.ai_disclosure_enabled:
        asset.ai_disclosure = json.dumps({"labeled": False})
    else:
        asset.ai_disclosure = json.dumps(
            {
                "labeled": True,
                "label_text": user_settings.ai_label_text,
                "position": user_settings.ai_label_position,
                "labeled_at": datetime.now(UTC).isoformat(),
            }
        )

    session.add(asset)
    return asset


def apply_labels_to_campaign(campaign_id: int, user: User, session: Session) -> int:
    """Apply AI disclosure labels to all assets in a campaign. Returns count of labeled assets."""
    user_settings = session.exec(
        select(UserSettings).where(UserSettings.user_id == user.id)
    ).first()
    if not user_settings:
        user_settings = UserSettings(user_id=user.id)
        session.add(user_settings)
        session.commit()
        session.refresh(user_settings)

    statement = select(Asset).where(Asset.campaign_id == campaign_id)
    assets = session.exec(statement).all()

    count = 0
    for asset in assets:
        apply_ai_label(asset, user_settings, session)
        count += 1

    session.commit()
    return count


def get_disclosure_metadata(asset: Asset) -> dict:
    """Parse asset AI disclosure JSON and return C2PA-compatible metadata dict."""
    try:
        disclosure = json.loads(asset.ai_disclosure)
    except (json.JSONDecodeError, TypeError):
        disclosure = {}

    return {
        "labeled": disclosure.get("labeled", False),
        "label_text": disclosure.get("label_text", ""),
        "position": disclosure.get("position", "NONE"),
        "ai_generated": True,
        "tool": "OpenSNS",
        "model": disclosure.get("model", "unknown"),
        "timestamp": disclosure.get("labeled_at", datetime.now(UTC).isoformat()),
    }
