from fastapi import  Depends, HTTPException
from datetime import datetime
from typing import List
from uuid import UUID
from pydantic import BaseModel

from core.services.campaign_service import CampaignService
from core.models.errors import POSException
from infra.api.app import app
from runner.dependencies import get_campaign_service


class CampaignCreate(BaseModel):
    name: str
    campaign_type: str
    start_date: datetime
    end_date: datetime
    rules: dict

class CampaignResponse(BaseModel):
    id: UUID
    name: str
    campaign_type: str
    start_date: datetime
    end_date: datetime
    is_active: bool
    rules: dict

@app.post("/campaigns", response_model=CampaignResponse)
def create_campaign(
    campaign_data: CampaignCreate,
    campaign_service: CampaignService = Depends(get_campaign_service)
) -> CampaignResponse:
    try:
        campaign = campaign_service.create_campaign(
            name=campaign_data.name,
            campaign_type=campaign_data.campaign_type,
            start_date=campaign_data.start_date,
            end_date=campaign_data.end_date,
            rules=campaign_data.rules
        )
        return CampaignResponse(
            id=campaign.id,
            name=campaign.name,
            campaign_type=campaign.campaign_type.value,
            start_date=campaign.start_date,
            end_date=campaign.end_date,
            is_active=campaign.is_active,
            rules=campaign.rules
        )
    except POSException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)

@app.get("/campaigns", response_model=List[CampaignResponse])
def list_campaigns(
    campaign_service: CampaignService = Depends(get_campaign_service)
) -> List[CampaignResponse]:
    try:
        campaigns = campaign_service.get_active_campaigns()
        return [
            CampaignResponse(
                id=c.id,
                name=c.name,
                campaign_type=c.campaign_type.value,
                start_date=c.start_date,
                end_date=c.end_date,
                is_active=c.is_active,
                rules=c.rules
            )
            for c in campaigns
        ]
    except POSException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)

@app.delete("/campaigns/{campaign_id}")
def deactivate_campaign(
    campaign_id: UUID,
    campaign_service: CampaignService = Depends(get_campaign_service)
) -> dict:
    try:
        campaign_service.deactivate_campaign(campaign_id)
        return {"message": "Campaign deactivated successfully"}
    except POSException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)