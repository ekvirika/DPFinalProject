from typing import Any, Dict
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from starlette import status

from core.models.campaign import Campaign, CampaignType
from core.services.campaign_service import CampaignService
from core.services.product_service import ProductService
from infra.api.schemas.campaign import (
    CampaignCreate,
    CampaignResponse,
)
from runner.dependencies import get_campaign_service, get_product_service

router = APIRouter()


@router.post(
    "/campaigns",
    response_model=Dict[str, CampaignResponse],
    status_code=status.HTTP_201_CREATED,
)
def create_campaign(
    campaign: CampaignCreate,
    campaign_service: CampaignService = Depends(get_campaign_service),
    product_service: ProductService = Depends(get_product_service),
) -> Dict[str, Any]:
    try:
        # Validate rules based on campaign type
        if campaign.campaign_type == CampaignType.DISCOUNT.value:
            if not isinstance(campaign.rules, dict):
                rules_dict = campaign.rules.dict()
            else:
                rules_dict = campaign.rules

            if rules_dict["routerlies_to"] == "product" and not rules_dict.get(
                "product_ids"
            ):
                raise ValueError("Product IDs must be provided for product discount")

            if rules_dict["routerlies_to"] == "receipt" and not rules_dict.get(
                "min_amount"
            ):
                raise ValueError("Minimum amount must be provided for receipt discount")

            # Check if products exist
            if rules_dict.get("product_ids"):
                for product_id in rules_dict["product_ids"]:
                    if not product_service.get_product(product_id):
                        raise ValueError(f"Product with ID '{product_id}' not found")

        elif campaign.campaign_type == CampaignType.BUY_N_GET_N.value:
            if not isinstance(campaign.rules, dict):
                rules_dict = campaign.rules.dict()
            else:
                rules_dict = campaign.rules

            # Check if products exist
            if not product_service.get_product(rules_dict["buy_product_id"]):
                raise ValueError(
                    f"Buy product with ID '{rules_dict['buy_product_id']}' not found"
                )

            if not product_service.get_product(rules_dict["get_product_id"]):
                raise ValueError(
                    f"Get product with ID '{rules_dict['get_product_id']}' not found"
                )

        elif campaign.campaign_type == CampaignType.COMBO.value:
            if not isinstance(campaign.rules, dict):
                rules_dict = campaign.rules.dict()
            else:
                rules_dict = campaign.rules

            # Check if products exist
            for product_id in rules_dict["product_ids"]:
                if not product_service.get_product(product_id):
                    raise ValueError(f"Product with ID '{product_id}' not found")

        # Create campaign
        if not isinstance(campaign.rules, dict):
            rules_dict = campaign.rules.dict()
        else:
            rules_dict = campaign.rules

        new_campaign = campaign_service.create_campaign(
            campaign.name, campaign.campaign_type, rules_dict
        )

        return {"campaign": new_campaign}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}",
        )


@router.delete("/campaigns/{campaign_id}")
def deactivate_campaign(
    campaign_id: UUID, campaign_service: CampaignService = Depends(get_campaign_service)
) -> Dict[str, Any]:
    # Don't check the return value since deactivate_campaign returns None
    campaign_service.deactivate_campaign(campaign_id)
    return {}


@router.get("/campaigns")
def list_campaigns(
    campaign_service: CampaignService = Depends(get_campaign_service),
) -> dict[str, list[Campaign]]:
    campaigns = campaign_service.get_all_campaigns()
    return {"campaigns": campaigns}


# Remove the duplicate class definition
# class CampaignService:
#     pass


@router.get("/campaigns/{campaign_id}", response_model=Dict[str, CampaignResponse])
def get_campaign(
    campaign_id: UUID, campaign_service: CampaignService = Depends(get_campaign_service)
) -> Dict[str, Campaign]:
    campaign = campaign_service.get_campaign(campaign_id)
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Campaign with ID '{campaign_id}' not found",
        )
    return {"campaign": campaign}
