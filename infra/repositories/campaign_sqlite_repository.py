import json
import sqlite3
from datetime import datetime
from typing import List
from uuid import UUID, uuid4

from core.models.campaign import Campaign, CampaignType
from core.models.errors import CampaignDatabaseError, CampaignNotFoundError
from core.models.repositories.campaign_repository import CampaignRepository
from infra.db.database import Database


class SQLiteCampaignRepository(CampaignRepository):
    def __init__(self, database: Database):
        self.database = database

    def create(self, campaign: Campaign) -> Campaign:
        """Create a new campaign and store it in the database."""
        try:
            with self.database.get_connection() as conn:
                campaign.id = uuid4()
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO campaigns (
                        id, type, name, start_date,
                         end_date, conditions, is_active, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        str(campaign.id),
                        campaign.type.value,
                        campaign.name,
                        campaign.start_date.isoformat(),
                        campaign.end_date.isoformat(),
                        json.dumps(campaign.conditions),
                        campaign.is_active,
                        datetime.now().isoformat(),
                    ),
                )
                conn.commit()
                return campaign
        except Exception as e:
            raise CampaignDatabaseError(f"Failed to create campaign: {str(e)}")

    def get_by_id(self, campaign_id: UUID) -> Campaign:
        """Retrieve a campaign by its unique ID."""
        try:
            with self.database.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT id, type, name, start_date, end_date, 
                    conditions, is_active 
                    FROM campaigns 
                    WHERE id = ?
                    """,
                    (str(campaign_id),),
                )
                row = cursor.fetchone()
                if not row:
                    raise CampaignNotFoundError(
                        f"Campaign with ID {campaign_id} not found."
                    )
                return self._row_to_campaign(row)
        except CampaignNotFoundError:
            raise  # Re-raise to ensure proper handling by the service layer.
        except Exception as e:
            raise CampaignDatabaseError(f"Failed to get campaign: {str(e)}")

    def get_active_campaigns(self) -> List[Campaign]:
        """Retrieve all active campaigns."""
        try:
            with self.database.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT id, type,
                     name, start_date, 
                     end_date, conditions, is_active 
                    FROM campaigns 
                    WHERE is_active = 1 
                    AND datetime('now') BETWEEN
                     datetime(start_date) AND datetime(end_date)
                    """
                )
                rows = cursor.fetchall()
                if not rows:
                    raise CampaignNotFoundError("No active campaigns found.")
                return [self._row_to_campaign(row) for row in rows]
        except CampaignNotFoundError:
            raise  # Re-raise to ensure proper handling by the service layer.
        except Exception as e:
            raise CampaignDatabaseError(f"Failed to get active campaigns: {str(e)}")

    def deactivate(self, campaign_id: UUID) -> None:
        """Deactivate a campaign by its ID."""
        try:
            with self.database.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    UPDATE campaigns 
                    SET is_active = 0 
                    WHERE id = ?
                    """,
                    (str(campaign_id),),
                )
                conn.commit()
                if cursor.rowcount == 0:
                    raise CampaignNotFoundError(
                        f"Campaign with ID {campaign_id} not found."
                    )
        except CampaignNotFoundError:
            raise  # Re-raise to ensure proper handling by the service layer.
        except Exception as e:
            raise CampaignDatabaseError(f"Failed to deactivate campaign: {str(e)}")

    def _row_to_campaign(self, row: sqlite3.Row) -> Campaign:
        """Convert a database row to a Campaign object."""
        try:
            return Campaign(
                id=UUID(row["id"]),
                name=row["name"],
                type=CampaignType(row["type"]),
                start_date=datetime.fromisoformat(row["start_date"]),
                end_date=datetime.fromisoformat(row["end_date"]),
                is_active=bool(row["is_active"]),
                conditions=json.loads(row["conditions"]),
                created_at=datetime.fromisoformat(row["created_at"]),
            )
        except (ValueError, json.JSONDecodeError) as e:
            raise CampaignDatabaseError(f"Failed to parse campaign data: {str(e)}")
