from fastapi import APIRouter, Depends
from core.models.campaign import Campaign, CampaignType
from core.models.errors import ProductNotFoundException, InvalidCampaignRulesException
from core.services.campaign_service import CampaignService
from core.services.product_service import ProductService
from infra.api.schemas.campaign import CampaignCreate, CampaignResponse
from runner.dependencies import get_campaign_service, get_product_service
from uuid import UUID
from typing import Any, Dict

router = APIRouter()


@router.post("/", response_model=Dict[str, CampaignResponse])
def create_campaign(
    campaign: CampaignCreate,
    campaign_service: CampaignService = Depends(get_campaign_service),) -> Dict[str, Any]:
    rules_dict = campaign.rules.dict() if not isinstance(campaign.rules, dict) else campaign.rules
    # No validation here, let repository handle errors
    new_campaign = campaign_service.create_campaign(campaign.name, campaign.campaign_type, rules_dict)
    return {"campaign": new_campaign}


@router.delete("/{campaign_id}")
def deactivate_campaign(
    campaign_id: UUID,
    campaign_service: CampaignService = Depends(get_campaign_service)
) -> Dict[str, Any]:
    # No validation here, let repository handle errors
    campaign_service.deactivate_campaign(campaign_id)
    return {}


@router.get("/")
def list_campaigns(
    campaign_service: CampaignService = Depends(get_campaign_service)
) -> Dict[str, list[Campaign]]:
    return {"campaigns": campaign_service.get_all_campaigns()}


@router.get("/{campaign_id}", response_model=Dict[str, CampaignResponse])
def get_campaign(
    campaign_id: UUID,
    campaign_service: CampaignService = Depends(get_campaign_service)
) -> Dict[str, Campaign]:
    # No validation here, let repository handle errors
    campaign = campaign_service.get_campaign(campaign_id)
    return {"campaign": campaign}