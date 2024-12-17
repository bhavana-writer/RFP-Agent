import logging
from simple_salesforce import Salesforce, SalesforceAuthenticationFailed
from app.config import settings

# Initialize logging
logger = logging.getLogger(__name__)


class SalesforceService:
    """
    Service to interact with Salesforce for account and related data management.
    """

    def __init__(self):
        """
        Initialize the SalesforceService with credentials from the configuration.
        """
        try:
            self.sf = Salesforce(
                username=settings.SALESFORCE_USERNAME,
                password=settings.SALESFORCE_PASSWORD,
                security_token=settings.SALESFORCE_SECURITY_TOKEN,
                domain=settings.SALESFORCE_DOMAIN
            )
            logger.info("Successfully authenticated with Salesforce.")
        except SalesforceAuthenticationFailed as e:
            logger.error(f"Failed to authenticate with Salesforce: {e}")
            raise e

    def search_accounts(self, search_term):
        """
        Search for accounts in Salesforce based on a search term.

        :param search_term: The search term (e.g., account name, partial name).
        :return: List of matching accounts.
        """
        try:
            # Properly format the SOSL query
            sosl_query = f"FIND {{{search_term}}} IN ALL FIELDS RETURNING Account(Id, Name, Industry)"
            result = self.sf.search(sosl_query)  # Use 'search' for SOSL queries
            accounts = result.get("searchRecords", [])
            return accounts
        except Exception as e:
            logger.error(f"Error searching for accounts: {e}")
            return None

    def create_task_for_account(self, account_id, subject, status="Not Started", activity_date=None):
        """
        Create a task for a specific Salesforce account.

        :param account_id: Salesforce Account ID.
        :param subject: Subject of the task.
        :param status: Status of the task (default: "Not Started").
        :param activity_date: Date of the task activity (YYYY-MM-DD, optional).
        :return: Created task details or None if an error occurs.
        """
        try:
            task_data = {
                "Subject": subject,
                "Status": status,
                "WhatId": account_id,  # Link the task to the account
            }
            if activity_date:
                task_data["ActivityDate"] = activity_date

            # Create task
            result = self.sf.Task.create(task_data)
            logger.info(f"Task created successfully: {result}")
            return result
        except Exception as e:
            logger.error(f"Error creating task for account {account_id}: {e}")
            return None


    def get_account_data(self, account_id):
        """
        Retrieve all associated data (contacts, cases, opportunities, activities) for a given account.

        :param account_id: Salesforce Account ID.
        :return: A detailed string summary of account data.
        """
        try:
            # Fetch account details
            account_details = self.sf.Account.get(account_id)
            account_summary = "Account Data from Salesforce\n\nAccount Details:\n"
            account_summary += "\n".join([f"{key}: {value}" for key, value in account_details.items()])

            # Fetch related contacts
            contacts_query = f"SELECT Id, Name, Email FROM Contact WHERE AccountId = '{account_id}'"
            contacts = self.sf.query_all(contacts_query)["records"]
            account_summary += "\n\nContacts:\n"
            account_summary += "\n".join([f"Name: {c.get('Name')}, Email: {c.get('Email')}" for c in contacts])

            # Fetch related cases
            cases_query = f"SELECT Id, Subject, Status FROM Case WHERE AccountId = '{account_id}'"
            cases = self.sf.query_all(cases_query)["records"]
            account_summary += "\n\nCases:\n"
            account_summary += "\n".join([f"Subject: {c.get('Subject')}, Status: {c.get('Status')}" for c in cases])

            # Fetch related opportunities
            opportunities_query = f"SELECT Id, Name, StageName, Amount FROM Opportunity WHERE AccountId = '{account_id}'"
            opportunities = self.sf.query_all(opportunities_query)["records"]
            account_summary += "\n\nOpportunities:\n"
            account_summary += "\n".join([f"Name: {o.get('Name')}, Stage: {o.get('StageName')}, Amount: {o.get('Amount')}" for o in opportunities])

            # Fetch related activities (tasks)
            activities_query = f"SELECT Id, Subject, Status, ActivityDate FROM Task WHERE WhatId = '{account_id}'"
            activities = self.sf.query_all(activities_query)["records"]
            account_summary += "\n\nActivities:\n"
            account_summary += "\n".join([f"Subject: {a.get('Subject')}, Status: {a.get('Status')}, Date: {a.get('ActivityDate')}" for a in activities])

            return account_summary
        except Exception as e:
            logger.error(f"Error fetching account data for ID {account_id}: {e}")
            return None

    def get_contacts_by_account(self, account_id):
        """
        Fetch all contacts related to a specific account.

        :param account_id: Salesforce Account ID.
        :return: List of contacts.
        """
        try:
            query = f"SELECT Id, Name, Email FROM Contact WHERE AccountId = '{account_id}'"
            result = self.sf.query_all(query)
            contacts = result.get("records", [])
            return contacts
        except Exception as e:
            logger.error(f"Error fetching contacts for account ID {account_id}: {e}")
            return None

    def get_opportunities_by_account(self, account_id):
        """
        Fetch all opportunities related to a specific account.

        :param account_id: Salesforce Account ID.
        :return: List of opportunities.
        """
        try:
            query = f"SELECT Id, Name, StageName, Amount FROM Opportunity WHERE AccountId = '{account_id}'"
            result = self.sf.query_all(query)
            opportunities = result.get("records", [])
            return opportunities
        except Exception as e:
            logger.error(f"Error fetching opportunities for account ID {account_id}: {e}")
            return None

    def get_cases_by_account(self, account_id):
        """
        Fetch all cases related to a specific account.

        :param account_id: Salesforce Account ID.
        :return: List of cases.
        """
        try:
            query = f"SELECT Id, Subject, Status FROM Case WHERE AccountId = '{account_id}'"
            result = self.sf.query_all(query)
            cases = result.get("records", [])
            return cases
        except Exception as e:
            logger.error(f"Error fetching cases for account ID {account_id}: {e}")
            return None

    def get_tasks_by_account(self, account_id):
        """
        Fetch all tasks related to a specific account.

        :param account_id: Salesforce Account ID.
        :return: List of tasks.
        """
        try:
            query = f"SELECT Id, Subject, Status, ActivityDate FROM Task WHERE WhatId = '{account_id}'"
            result = self.sf.query_all(query)
            tasks = result.get("records", [])
            return tasks
        except Exception as e:
            logger.error(f"Error fetching tasks for account ID {account_id}: {e}")
            return None
    def add_note_to_account(self, account_id, title, body):
        """
        Add a Note to a specific Salesforce account.

        :param account_id: Salesforce Account ID.
        :param title: Title of the note.
        :param body: Content/body of the note.
        :return: Created note details or None if an error occurs.
        """
        try:
            note_data = {
                "Title": title,
                "Body": body,
                "ParentId": account_id  # Link the note to the account
            }

            # Create Note
            result = self.sf.Note.create(note_data)
            logger.info(f"Note added successfully: {result}")
            return result
        except Exception as e:
            logger.error(f"Error adding note to account {account_id}: {e}")
            return None
