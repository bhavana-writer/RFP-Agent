import writer
print(dir(writer))
from app.services.google_trends_service import GoogleTrendsService
from writerai import Writer
import json
from dotenv import load_dotenv
import os
from app.config import settings
from app.services.salesforce_service import SalesforceService
from app.services.slack_service import post_canvas_message
import requests
import logging
import writer as wf
import pandas as pd
import time



# Initialize logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)



# Load environment variables from .env file
load_dotenv(override=True)

# Base URL for the application
# Base URL for the application (now dynamically set)
base_url = settings.BASE_URL
print(f"Base URL initialized: {base_url}")



# This is a placeholder to get you started or refresh your memory.
# Delete it or adapt it as necessary.
# Documentation is available at https://dev.writer.com/framework

# Shows in the log when the app starts
print("Hello world!")

#Workflow configuration
wf.Config.feature_flags = ["workflows", "custom_block_icons", "dataframeEditor"]


base_url = settings.BASE_URL
print(f"Base URL initialized 2: {base_url}")
writer_abm_app_id = "3d099a02-7089-4ef2-9189-168e2af29edc"
writer_sales_summary_app_id = "10531b49-35a9-4dc0-8517-a67d4a08a19d"
transcript_graph_id="6940e9ca-903f-46cf-8129-26f4812d0c43"

# "_my_private_element" won't be serialised or sent to the frontend,
# because it starts with an underscore

#Define State for RFP Dataframe
# Define RFP DataFrame schema
rfp_df = pd.DataFrame([
    {
        'Index': 0,
        'Question': 'Based on Trader Joe\'s employee demographics and the current healthcare trends, how would you tailor a benefits package that aligns with our values of cost-efficiency, employee satisfaction, and wellness innovation?',
        'Answer': '',
        'Notes': '',
        'Approved': False
    },
    {
        'Index': 1,
        'Question': 'How does your approach to addressing rising healthcare costs for retail employees differ from competitors like [Competitor\'s Insurance Provider], and what unique strategies would you recommend for Trader Joe\'s workforce?',
        'Answer': '',
        'Notes': '',
        'Approved': False
    },
    {
        'Index': 2,
        'Question': 'What insights can you provide about Trader Joe\'s workforce health risks based on industry benchmarks, and how would you use those insights to design a targeted intervention program?',
        'Answer': '',
        'Notes': '',
        'Approved': False
    },
    {
        'Index': 3,
        'Question': 'Considering Trader Joe\'s focus on employee wellness and engagement, how would you integrate emerging healthcare technologies such as AI-powered analytics and wearable devices to enhance our benefits program?',
        'Answer': '',
        'Notes': '',
        'Approved': False
    },
    {
        'Index': 4,
        'Question': 'What are the key success metrics you would recommend for evaluating the effectiveness of a health insurance plan for Trader Joe\'s, and how do these metrics align with industry benchmarks and trends?',
        'Answer': '',
        'Notes': '',
        'Approved': False
    }
])

def generate_answer_object(question_index):
    """
    Generates an answer object for a specific RFP question including sources.
    
    :param question_index: Index of the question in the RFP DataFrame (0-4)
    :return: Dictionary containing the answer and sources
    """
    answers = {
        0: {
            "answer": """For Trader Joe's workforce of 50,000 employees nationwide, we propose a comprehensive benefits package that addresses the diverse needs of full-time, part-time, and seasonal workers. Our approach focuses on providing flexible health benefits with varying deductibles and premiums, complemented by comprehensive telehealth services and virtual mental health support. To promote wellness innovation, we've incorporated AI-powered health risk assessments and digital wellness challenges with rewards, alongside preventive care incentives. Cost efficiency is achieved through strategic value-based care partnerships, optimized prescription drug programs, and data-driven provider network management that ensures quality care while controlling expenses.""",
            "sources": ["Internal HR Data", "Kaiser Family Foundation Survey 2024", "Historical Claims Analysis"]
        },
        1: {
            "answer": """Our distinctive approach to managing healthcare costs for retail employees centers on retail-specific solutions that set us apart from competitors. We've developed a custom network design tailored to retail locations, implementing shift-based telehealth availability and bulk prescription programs that address the unique needs of retail workers. Our cost containment strategy leverages cutting-edge predictive analytics for claims management and AI-driven fraud detection, combined with value-based care arrangements. The employee experience is enhanced through a mobile-first engagement platform, ensuring 24/7 virtual care access and personalized wellness coaching that accommodates varying work schedules.""",
            "sources": ["AHIP Competitive Analysis 2024", "United Health Case Studies", "Retail Benefits Benchmark Study"]
        },
        2: {
            "answer": """Analysis of retail industry benchmarks reveals significant health risks specific to Trader Joe's workforce environment. Primary concerns include musculoskeletal issues from prolonged standing and lifting, elevated stress levels and mental health challenges, and irregular sleep patterns due to shift work schedules. To address these risks, we've designed a comprehensive intervention program featuring ergonomic training programs and 24/7 mental health support services. Our preventive measures incorporate on-site health screenings, personalized wellness coaching, and targeted stress management workshops, creating a holistic approach to employee health management.""",
            "sources": ["Retail Industry Health Data", "OSHA Reports", "Wellness Program Analytics"]
        },
        3: {
            "answer": """Our technology integration strategy leverages cutting-edge healthcare innovations to enhance Trader Joe's benefits program. At its core, we implement AI-powered solutions including predictive health risk modeling, personalized wellness recommendations, and smart claims processing. The wearable technology component features activity tracking incentives, sleep quality monitoring, and stress level indicators, all designed to promote proactive health management. Digital engagement is facilitated through a comprehensive mobile health app, virtual health coaching services, and real-time benefits tracking, ensuring employees stay connected and engaged with their health benefits.""",
            "sources": ["Digital Health Trends Report", "Wearable Technology Studies", "Employee Engagement Metrics"]
        },
        4: {
            "answer": """To evaluate the effectiveness of Trader Joe's health insurance plan, we focus on three key metric categories. Financial metrics track healthcare cost per employee, claims ratio trends, and prescription drug spending to ensure cost efficiency. Utilization metrics monitor preventive care participation, telehealth adoption rates, and overall wellness program engagement to gauge program effectiveness. Outcome metrics measure employee satisfaction scores, track improvements in health risk assessments, and monitor absenteeism reduction, providing a comprehensive view of the program's impact on employee health and wellbeing.""",
            "sources": ["Healthcare Analytics Data", "Industry Benchmarks 2024", "Employee Satisfaction Surveys"]
        }
    }
    
    return answers.get(question_index, {
        "answer": "Answer not yet available",
        "sources": ["Pending"]
    })

def update_rfp_answer(state, question_index, payload=None):
    """
    Updates the RFP DataFrame with answer for the selected question.
    Shows loading message and adds delay before update.
    
    :param state: Application state dictionary
    :param question_index: Index of the question to answer (0-4) 
    :param payload: Optional payload data from the event
    """
    try:
        print(f"Received payload: {payload}")
        print(f"Initial question_index: {question_index}")
        
        # Extract record_index from question_index if it's a dict
        if isinstance(question_index, dict) and 'record_index' in question_index:
            question_index = question_index['record_index']
            print(f"Index from record_index: {question_index}")
        # Extract index from payload if present
        elif isinstance(payload, dict) and 'index' in payload:
            question_index = payload['index']
            print(f"Index from payload dict: {question_index}")
            
        # Ensure we have a valid integer index
        if question_index is None:
            raise ValueError("No valid question index provided in payload or arguments")
            
        # Convert question_index to int
        try:
            question_index = int(question_index)
            print(f"Converted question_index to int: {question_index}")
        except (ValueError, TypeError) as e:
            raise ValueError(f"Could not convert question_index to integer: {e}")
        
        # Validate index is within bounds
        if question_index < 0 or question_index >= len(rfp_df):
            raise ValueError(f"Question index {question_index} is out of bounds")
            
        print(f"Processing question index: {question_index}")

        # Update state to show searching message
        state["message_status"] = "%Searching through knowledge sources..."
        time.sleep(2)
        
        # Update state to show generating message
        state["message_status"] = "%Generating comprehensive answer..."
        time.sleep(2)
        
        # Generate answer object for selected question
        answer_obj = generate_answer_object(question_index)
        
        # Update DataFrame for selected question
        rfp_df.at[question_index, 'Answer'] = answer_obj["answer"]
        rfp_df.at[question_index, 'Notes'] = f"Sources: {', '.join(answer_obj['sources'])}"
        rfp_df.at[question_index, 'Approved'] = False
        
        # Store answer object and updated DataFrame in state
        state["answer_object"] = answer_obj
        state["rfp_df"] = rfp_df
        
        # Update state with success message
        state["message_status"] = "+Answer generated successfully!"
        print(f"Successfully updated answer for question {question_index}")
        
    except Exception as e:
        print(f"Error updating RFP answer: {e}")
        state["message_status"] = f"-Error generating answer: {str(e)}"
        state["answer_object"] = {"error": str(e)}

# Initialize the application state
state = wf.init_state({
    "my_app": {"title": "AI Workflow"},
    "accounts": {},  # Preloaded accounts
    "selected_account_id": None,  # Tracks the ID of the selected account
    "base_url": base_url,  # Set Base URL in the state
    "account_name": "",  # Name of the selected account
    "account_api_url": "",  # API URL for fetching account data
    "account_search_api_url": "",  # API URL for searching news
    "sf_account_data": "",  # Data for the selected account
    "kg_api_url": f"{base_url}/kg-question",  # URL for Knowledge Graph API
    "create_canvas_url": f"{base_url}/create-account-briefing",  # URL for creating a Salesforce Canvas app
    "kg_data": "",  # Data from the Knowledge Graph API
    "combined_account_data": "",  # Combined data from Salesforce and Knowledge Graph
    "executive_summary": "",  # Executive summary of the combined data
    "writer_abm_app_id": writer_abm_app_id,  # Writer app ID for ABM content
    "writer_sales_summary_app_id": writer_sales_summary_app_id,  # Writer app ID for Sales Summary content
    "transcript_graph_id": transcript_graph_id,  # Graph ID for the transcript
    "transcript_url": f"{base_url}/api/v1/writer/question-graph",  # URL for the transcript
    "abm_content": "",  # ABM content generated by Writer
    "input_content_brief": "Explore the impact of technology on modern communication",
    "input_brand_tone": "Professional",
    "input_target_audience": "Tech Enthusiasts",
    "input_key_message": "Innovation is the key to success in the modern business landscape",
    "output_article_text": "",
    "firefly_instructions": "",
    "firefly_api_url": f"{base_url}/api/v1/firefly/generate-image",
    "output_firefly_image": "",
    "rfp_df": rfp_df.assign(Answer='', Notes=''),  # Initialize DataFrame with empty answers and notes
    "answer_object": "",
    "message_status": "",  # Status message for RFP answer generation,
    "rfp_table_style": "rfp_table",  # Custom stylesheet name
    "uhg_image_url": "static/uhg_logo.png"
})

# Import the custom stylesheet
state.import_stylesheet("rfp_table", "/static/rfp_table.css")

def preload_accounts(state):
    """
    Fetch all accounts from Salesforce and store them in the state as { "account_id": "account_name" }.
    """
    print("Handler: preload_accounts | Start")
    try:
        # Initialize SalesforceService
        salesforce_service = SalesforceService()

        # Fetch all accounts
        query = "SELECT Id, Name FROM Account"
        results = salesforce_service.sf.query_all(query)

        # Parse results into the required format
        accounts_dict = {account["Id"]: account["Name"] for account in results["records"]}

        # Store the parsed accounts in the state
        state["accounts"] = accounts_dict
        print(f"Handler: preload_accounts | Loaded {len(accounts_dict)} accounts")

    except Exception as e:
        state["accounts"] = {}
        print(f"Error in preload_accounts: {e}")

    print("Handler: preload_accounts | End")


def handle_selection(state, payload):
    """
    Updates the state with the selected account ID, account name, and relevant URLs.
    """
    print("Payload received:", payload)

    # Extract selected_account_id from payload
    if isinstance(payload, str):
        selected_account_id = payload
    elif isinstance(payload, dict):
        selected_account_id = payload.get("selected_account_id")
    else:
        print(f"Unexpected payload type: {type(payload)}. Exiting handler.")
        return  # Exit early for invalid payloads

    print(f"Handler: handle_selection | Selected Account ID: {selected_account_id}")

    # Retrieve account name using selected_account_id
    try:
        account_name = state["accounts"][selected_account_id]
    except KeyError:
        print(f"Account ID {selected_account_id} not found in preloaded accounts.")
        return

    state["selected_account_id"] = selected_account_id
    state["account_name"] = account_name

    # Ensure Base URL is set
    base_url = state["base_url"] if "base_url" in state else None
    if not base_url:
        print("Base URL is not set in state. Exiting handler.")
        return  # Exit gracefully if Base URL is unavailable

    # Update API URLs based on selected account
    state["account_api_url"] = f"{base_url}/api/v1/salesforce/account/{selected_account_id}"
    state["account_search_api_url"] = f"{base_url}/api/v1/tavily/search-news/{account_name.replace(' ', '%20')}"

    # Logging updates
    print("State Updated:")
    print(f"  - selected_account_id = {state['selected_account_id']}")
    print(f"  - account_name = {state['account_name']}")
    print(f"  - account_api_url = {state['account_api_url']}")
    print(f"  - account_search_api_url = {state['account_search_api_url']}")
    print(state)

def send_multiple_canvas_urls():
    """
    Sends two Canvas URLs to a specified Slack channel.
    """
    channel_id = "C08476AM146"
    canvas_urls = [
        "https://writerai.slack.com/docs/T02AJRK99/F084ZCPM6M6",
        "https://writerai.slack.com/docs/T02AJRK99/F084G721PGB"
    ]
    
    for canvas_url in canvas_urls:
        response = post_canvas_message(canvas_url, channel_id)
        if "error" in response:
            logger.error(f"Failed to send canvas URL: {canvas_url}, Error: {response['error']}")
        else:
            logger.info(f"Successfully sent canvas URL: {canvas_url}")

def search_and_fetch_account_data(search_term):
    """
    Search for a Salesforce account using a search term and fetch detailed account data.
    """
    logger.info("Handler: search_and_fetch_account_data | Start")
    salesforce_service = SalesforceService()
    try:
        # Search for accounts
        logger.info(f"Searching for accounts with term: '{search_term}'")
        accounts = salesforce_service.search_accounts(search_term)
        if not accounts:
            logger.warning(f"No accounts found for search term: '{search_term}'")
            return "No accounts found"
        
        # Display matching accounts
        logger.info(f"Found {len(accounts)} account(s):")
        for idx, account in enumerate(accounts, start=1):
            logger.info(f"{idx}. Account Name: {account['Name']} | ID: {account['Id']}")

        # Fetch details for the first account
        selected_account_id = accounts[0]['Id']
        logger.info(f"Fetching data for Account ID: {selected_account_id}")
        account_data = salesforce_service.get_account_data(selected_account_id)
        
        if account_data:
            logger.info("Successfully fetched account data.")
            return account_data
        else:
            logger.warning(f"Failed to fetch data for Account ID: {selected_account_id}")
            return "Failed to fetch account data"
    except Exception as e:
        logger.error(f"Error in search_and_fetch_account_data: {e}")
        return f"Error: {str(e)}"
    finally:
        logger.info("Handler: search_and_fetch_account_data | End")
def search_account_and_create_task(state, search_term, task_subject, task_status="Not Started", task_date=None):
    """
    Search for an account by name, retrieve the ID, and create a task for it.

    :param state: Application state.
    :param search_term: Search term for the account name.
    :param task_subject: Subject of the task to be created.
    :param task_status: Status of the task.
    :param task_date: Task activity date in YYYY-MM-DD format.
    """
    print("Handler: search_account_and_create_task | Start")

    try:
        # Initialize SalesforceService
        salesforce_service = SalesforceService()

        # Search for accounts matching the search term
        accounts = salesforce_service.search_accounts(search_term)
        if not accounts:
            print(f"No accounts found for search term: {search_term}")
            return

        # Use the first matching account
        account = accounts[0]
        account_id = account["Id"]
        account_name = account["Name"]
        print(f"Found Account: {account_name} (ID: {account_id})")

        # Create a task for the account
        result = salesforce_service.create_task_for_account(
            account_id=account_id,
            subject=task_subject,
            status=task_status,
            activity_date=task_date
        )

        if result:
            print(f"Task created successfully for account {account_name}: {result}")
            state["task_creation_status"] = f"Task created for account '{account_name}'"
        else:
            print(f"Failed to create task for account '{account_name}'")
            state["task_creation_status"] = f"Failed to create task for account '{account_name}'"

    except Exception as e:
        print(f"Error in search_account_and_create_task: {e}")
        state["task_creation_status"] = f"Error: {str(e)}"

    print("Handler: search_account_and_create_task | End")

def search_account_and_add_note(state, search_term, note_title, note_body):
    """
    Search for an account by name, retrieve the ID, and add a note to it.

    :param state: Application state.
    :param search_term: Search term for the account name.
    :param note_title: Title of the note.
    :param note_body: Content of the note.
    """
    print("Handler: search_account_and_add_note | Start")

    try:
        # Initialize SalesforceService
        salesforce_service = SalesforceService()

        # Search for accounts matching the search term
        accounts = salesforce_service.search_accounts(search_term)
        if not accounts:
            print(f"No accounts found for search term: {search_term}")
            return

        # Use the first matching account
        account = accounts[0]
        account_id = account["Id"]
        account_name = account["Name"]
        print(f"Found Account: {account_name} (ID: {account_id})")

        # Add a note to the account
        result = salesforce_service.add_note_to_account(
            account_id=account_id,
            title=note_title,
            body=note_body
        )

        if result:
            print(f"Note added successfully for account {account_name}: {result}")
            state["note_creation_status"] = f"Note added to account '{account_name}'"
        else:
            print(f"Failed to add note for account '{account_name}'")
            state["note_creation_status"] = f"Failed to add note to account '{account_name}'"

    except Exception as e:
        print(f"Error in search_account_and_add_note: {e}")
        state["note_creation_status"] = f"Error: {str(e)}"

    print("Handler: search_account_and_add_note | End")

# Preload accounts during initialization
preload_accounts(state)
print("Preloaded accounts:", state["accounts"])

print(f"Current working directory: {os.getcwd()}")
print(f"Environment files in current directory: {[f for f in os.listdir() if '.env' in f]}")





