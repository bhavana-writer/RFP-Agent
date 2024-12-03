from pyairtable import Table
from app.config import settings
import logging

logger = logging.getLogger(__name__)

class AirtableService:
    def __init__(self):
        self.table = Table(settings.AIRTABLE_API_KEY, settings.AIRTABLE_BASE_ID, settings.AIRTABLE_TABLE_NAME)

    def get_records(self):
        try:
            records = self.table.all()
            logger.info(f"Fetched {len(records)} records from Airtable")
            return records
        except Exception as e:
            logger.error(f"Error fetching records: {e}")
            raise

    def create_record(self, data):
        try:
            record = self.table.create(data)
            logger.info(f"Created record: {record['id']}")
            return record
        except Exception as e:
            logger.error(f"Error creating record: {e}")
            raise

    def update_record(self, record_id, data):
        try:
            record = self.table.update(record_id, data)
            logger.info(f"Updated record: {record['id']}")
            return record
        except Exception as e:
            logger.error(f"Error updating record: {e}")
            raise

    def delete_record(self, record_id):
        try:
            self.table.delete(record_id)
            logger.info(f"Deleted record: {record_id}")
        except Exception as e:
            logger.error(f"Error deleting record: {e}")
            raise
