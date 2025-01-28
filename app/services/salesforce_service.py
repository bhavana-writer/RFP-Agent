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

    def total_pipeline_value(self):
        """
        Calculate the total pipeline value (sum of Amount for open opportunities).
        
        :return: Total pipeline value as a float
        """
        query = "SELECT SUM(Amount) FROM Opportunity WHERE IsClosed = FALSE"
        result = self.sf.query(query)
        total_value = result["records"][0].get("expr0", 0)
        return total_value

    def weighted_pipeline_value(self):
        """
        Calculate the weighted pipeline value (Amount * Probability for open opportunities).
        
        :return: Weighted pipeline value as a float
        """
        query = "SELECT SUM(Amount * Probability) FROM Opportunity WHERE IsClosed = FALSE"
        result = self.sf.query(query)
        weighted_value = result["records"][0].get("expr0", 0)
        return weighted_value

    def stage_wise_pipeline_breakdown(self):
        """
        Get the pipeline value grouped by stage.
        
        :return: Dictionary with stage names as keys and pipeline values as values
        """
        query = "SELECT StageName, SUM(Amount) FROM Opportunity WHERE IsClosed = FALSE GROUP BY StageName"
        result = self.sf.query(query)
        breakdown = {record["StageName"]: record["expr0"] for record in result["records"]}
        return breakdown

    def pipeline_velocity(self, average_deal_size, win_rate, sales_cycle_length):
        """
        Calculate the pipeline velocity.
        
        :param average_deal_size: Average size of deals in the pipeline
        :param win_rate: Win rate as a decimal (e.g., 0.25 for 25%)
        :param sales_cycle_length: Average sales cycle length in days
        :return: Pipeline velocity as a float
        """
        velocity = (len(self.sf.query("SELECT Id FROM Opportunity WHERE IsClosed = FALSE")["records"]) *
                    average_deal_size * win_rate) / sales_cycle_length
        return velocity

    def win_rate(self):
        """
        Calculate the win rate (percentage of closed-won opportunities).
        
        :return: Win rate as a float
        """
        closed_won_query = "SELECT COUNT(Id) FROM Opportunity WHERE IsClosed = TRUE AND IsWon = TRUE"
        total_query = "SELECT COUNT(Id) FROM Opportunity"
        closed_won_count = self.sf.query(closed_won_query)["records"][0].get("expr0", 0)
        total_count = self.sf.query(total_query)["records"][0].get("expr0", 1)
        return (closed_won_count / total_count) * 100

    def lost_opportunity_analysis(self):
        """
        Analyze lost opportunities grouped by CloseReason.
        
        :return: Dictionary with CloseReasons as keys and counts as values
        """
        query = "SELECT CloseReason, COUNT(Id) FROM Opportunity WHERE IsClosed = TRUE AND IsWon = FALSE GROUP BY CloseReason"
        result = self.sf.query(query)
        analysis = {record["CloseReason"]: record["expr0"] for record in result["records"]}
        return analysis

    def sales_cycle_length(self):
        """
        Calculate the average sales cycle length (days between CreatedDate and CloseDate).
        
        :return: Average sales cycle length in days as a float
        """
        query = "SELECT AVG(CloseDate - CreatedDate) FROM Opportunity WHERE IsClosed = TRUE AND IsWon = TRUE"
        result = self.sf.query(query)
        avg_cycle_length = result["records"][0].get("expr0", 0)
        return avg_cycle_length

    def forecast_by_close_date(self):
        """
        Forecast revenue grouped by CloseDate for open opportunities.
        
        :return: Dictionary with CloseDates as keys and forecasted revenue as values
        """
        query = "SELECT CloseDate, SUM(Amount) FROM Opportunity WHERE IsClosed = FALSE GROUP BY CloseDate"
        result = self.sf.query(query)
        forecast = {record["CloseDate"]: record["expr0"] for record in result["records"]}
        return forecast

    def pipeline_gap_analysis(self, target_revenue):
        """
        Perform a pipeline gap analysis (difference between target and total pipeline value).
        
        :param target_revenue: Target revenue as a float
        :return: Pipeline gap as a float
        """
        total_pipeline = self.total_pipeline_value()
        gap = target_revenue - total_pipeline
        return gap

    def conversion_rates_by_stage(self):
        """
        Calculate conversion rates by stage (opportunities moving to the next stage).
        
        :return: Dictionary with stage names and conversion rates
        """
        query = "SELECT StageName, COUNT(Id) FROM Opportunity WHERE IsClosed = FALSE GROUP BY StageName"
        result = self.sf.query(query)
        total_count = sum(record["expr0"] for record in result["records"])
        conversion_rates = {record["StageName"]: (record["expr0"] / total_count) * 100 for record in result["records"]}
        return conversion_rates
    
   