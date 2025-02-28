from typing import Any, Dict, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from core.models.campaign import Campaign
from core.models.errors import (
    CampaignNotFoundException,
    InvalidCampaignRulesException,
)
from core.services.campaign_service import CampaignService
from infra.api.schemas.campaign import CampaignCreate, CampaignResponse
from runner.dependencies import get_campaign_service

router = APIRouter()


@router.post("/", response_model=Dict[str, CampaignResponse])
def create_campaign(
    campaign: CampaignCreate,
    campaign_service: CampaignService = Depends(get_campaign_service),
) -> Dict[str, Any]:
    try:
        rules_dict = (
            campaign.rules.dict() if hasattr(campaign.rules, "dict") else campaign.rules
        )
        new_campaign = campaign_service.create_campaign(
            campaign.name, campaign.campaign_type, rules_dict
        )

        # Convert to response format
        return {"campaign": _campaign_to_response(new_campaign)}
    except InvalidCampaignRulesException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{campaign_id}", response_model=Dict[str, CampaignResponse])
def get_campaign(
    campaign_id: UUID, campaign_service: CampaignService = Depends(get_campaign_service)
) -> Dict[str, Any]:
    try:
        campaign = campaign_service.get_campaign(campaign_id)
        return {"campaign": _campaign_to_response(campaign)}
    except CampaignNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=Dict[str, List[CampaignResponse]])
def list_campaigns(
    campaign_service: CampaignService = Depends(get_campaign_service),
) -> Dict[str, List[Dict[str, Any]]]:
    try:
        campaigns = campaign_service.get_all_campaigns()
        return {
            "campaigns": [_campaign_to_response(campaign) for campaign in campaigns]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{campaign_id}")
def deactivate_campaign(
    campaign_id: UUID, campaign_service: CampaignService = Depends(get_campaign_service)
) -> Dict[str, Any]:
    try:
        campaign_service.deactivate_campaign(campaign_id)
        return {"success": True}
    except CampaignNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def _campaign_to_response(campaign: Campaign) -> Dict[str, Any]:
    """Convert Campaign domain object to API response format."""
    return {
        "id": campaign.id,
        "name": campaign.name,
        "campaign_type": campaign.campaign_type.value,
        "rules": campaign.rules.__dict__,
        "is_active": campaign.is_active,
    }
