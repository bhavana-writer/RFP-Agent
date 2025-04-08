import writer
# from app.services.google_trends_service import GoogleTrendsService
from writerai import Writer
import json
# from dotenv import load_dotenv
import os
# from app.config import settings
# from app.services.salesforce_service import SalesforceService
# from app.services.slack_service import post_canvas_message
import requests
# import logging
import writer as wf
import pandas as pd
import time



# Initialize logger
# logging.basicConfig(
#     level=logging.INFO,
#     format="%(asctime)s [%(levelname)s] %(message)s",
#     handlers=[logging.StreamHandler()]
# )
# logger = logging.getLogger(__name__)



# Load environment variables from .env file
# load_dotenv(override=True)

# Base URL for the application
# Base URL for the application (now dynamically set)
# base_url = settings.BASE_URL
# print(f"Base URL initialized: {base_url}")


#Workflow configuration
wf.Config.feature_flags = ["workflows", "custom_block_icons", "dataframeEditor"]


# base_url = settings.BASE_URL
# print(f"Base URL initialized 2: {base_url}")
# writer_abm_app_id = "3d099a02-7089-4ef2-9189-168e2af29edc"
# writer_sales_summary_app_id = "10531b49-35a9-4dc0-8517-a67d4a08a19d"
# transcript_graph_id="6940e9ca-903f-46cf-8129-26f4812d0c43"


#Define State for RFP Dataframe
# Define RFP DataFrame schema
rfp_df = pd.DataFrame([
    {
        'Index': 0,
        'Question': 'Please briefly describe your firm’s investment philosophy. How has it changed since the inception of this product?',
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


rfp_df_answered = pd.DataFrame([
    {
        'Index': 0,
        'Question': 'Please briefly describe your firm’s investment philosophy. How has it changed since the inception of this product?',
        'Answer': 'Our investment philosophy focuses on long-term value creation through active management, emphasizing fundamental research, global diversification, and risk-adjusted returns. Since inception, weve integrated quantitative models and ESG factors to complement our traditional approaches.',
        'Notes': 'Sources: Franklin Templeton Global Investment Committee Reports, Quarterly Market Outlooks from the Franklin Templeton Institute, Insights from Our Proprietary Quantitative Research Team',
        'Approved': False
    },
    {
        'Index': 1,
        'Question': 'Please discuss your firm’s investment strategy, screening processes, and portfolio construction methodology.',
        'Answer': 'We adopt a bottom-up, research-driven strategy supported by quantitative screening and macroeconomic analysis. Portfolios are constructed with a focus on diversification and risk management, incorporating sector, geographic, and asset class considerations. ',
        'Notes': 'Sources: Franklin Templeton Global Investment Committee Reports, Internal Sector Research from Our Global Analyst Network, Data from Proprietary Quantitative Screening Tools',
        'Approved': False
    },
    {
        'Index': 2,
        'Question': 'How do you decide to buy or sell a security?',
        'Answer': 'Buy decisions are based on attractive valuations, strong fundamentals, and positive macroeconomic indicators. Sell decisions are prompted by deteriorating fundamentals, overvaluation, or shifts in market conditions.',
        'Notes': 'Sources: Retail Industry Health Data, OSHA Reports, Wellness Program Analytics',
        'Approved': False
    },
    {
        'Index': 3,
        'Question': 'Please describe how your firm controls portfolio investment risk.',
        'Answer': 'We employ a multi-layered risk management framework combining diversification, sector limits, stress testing, and active monitoring of exposures to manage risk at both the security and portfolio levels.',
        'Notes': 'Sources: Franklin Templeton Global Investment Committee Reports, Internal Sector Research from Our Global Analyst Network, Data from Proprietary Quantitative Screening Tools',
        'Approved': False
    },
    {
        'Index': 4,
        'Question': 'Are portfolios managed by individual managers or teams?',
        'Answer': 'Portfolios are managed by collaborative teams of sector specialists, portfolio managers, and quantitative analysts to ensure diversified perspectives.',
        'Notes': 'Sources: Franklin Templeton Global Investment Committee Reports, Quarterly Market Outlooks from the Franklin Templeton Institute, Insights from Our Proprietary Quantitative Research Team',
        'Approved': False
    }
])



# def generate_answer_object(state):
#     """
#     Generates an answer object for a specific RFP question including sources.
    
#     :param question_index: Index of the question in the RFP DataFrame (0-4)
#     :return: Dictionary containing the answer and sources
#     """
#     answers = {
#         0: {
#             "answer": """For Trader Joe's workforce of 50,000 employees nationwide, we propose a comprehensive benefits package that addresses the diverse needs of full-time, part-time, and seasonal workers. Our approach focuses on providing flexible health benefits with varying deductibles and premiums, complemented by comprehensive telehealth services and virtual mental health support. To promote wellness innovation, we've incorporated AI-powered health risk assessments and digital wellness challenges with rewards, alongside preventive care incentives. Cost efficiency is achieved through strategic value-based care partnerships, optimized prescription drug programs, and data-driven provider network management that ensures quality care while controlling expenses.""",
#             "sources": ["Internal HR Data", "Kaiser Family Foundation Survey 2024", "Historical Claims Analysis"]
#         },
#         1: {
#             "answer": """Our distinctive approach to managing healthcare costs for retail employees centers on retail-specific solutions that set us apart from competitors. We've developed a custom network design tailored to retail locations, implementing shift-based telehealth availability and bulk prescription programs that address the unique needs of retail workers. Our cost containment strategy leverages cutting-edge predictive analytics for claims management and AI-driven fraud detection, combined with value-based care arrangements. The employee experience is enhanced through a mobile-first engagement platform, ensuring 24/7 virtual care access and personalized wellness coaching that accommodates varying work schedules.""",
#             "sources": ["AHIP Competitive Analysis 2024", "United Health Case Studies", "Retail Benefits Benchmark Study"]
#         },
#         2: {
#             "answer": """Analysis of retail industry benchmarks reveals significant health risks specific to Trader Joe's workforce environment. Primary concerns include musculoskeletal issues from prolonged standing and lifting, elevated stress levels and mental health challenges, and irregular sleep patterns due to shift work schedules. To address these risks, we've designed a comprehensive intervention program featuring ergonomic training programs and 24/7 mental health support services. Our preventive measures incorporate on-site health screenings, personalized wellness coaching, and targeted stress management workshops, creating a holistic approach to employee health management.""",
#             "sources": ["Retail Industry Health Data", "OSHA Reports", "Wellness Program Analytics"]
#         },
#         3: {
#             "answer": """Our technology integration strategy leverages cutting-edge healthcare innovations to enhance Trader Joe's benefits program. At its core, we implement AI-powered solutions including predictive health risk modeling, personalized wellness recommendations, and smart claims processing. The wearable technology component features activity tracking incentives, sleep quality monitoring, and stress level indicators, all designed to promote proactive health management. Digital engagement is facilitated through a comprehensive mobile health app, virtual health coaching services, and real-time benefits tracking, ensuring employees stay connected and engaged with their health benefits.""",
#             "sources": ["Digital Health Trends Report", "Wearable Technology Studies", "Employee Engagement Metrics"]
#         },
#         4: {
#             "answer": """To evaluate the effectiveness of Trader Joe's health insurance plan, we focus on three key metric categories. Financial metrics track healthcare cost per employee, claims ratio trends, and prescription drug spending to ensure cost efficiency. Utilization metrics monitor preventive care participation, telehealth adoption rates, and overall wellness program engagement to gauge program effectiveness. Outcome metrics measure employee satisfaction scores, track improvements in health risk assessments, and monitor absenteeism reduction, providing a comprehensive view of the program's impact on employee health and wellbeing.""",
#             "sources": ["Healthcare Analytics Data", "Industry Benchmarks 2024", "Employee Satisfaction Surveys"]
#         }
#     }
    
#     return answers.get(question_index, {
#         "answer": "Answer not yet available",
#         "sources": ["Pending"]
#     })

# def update_rfp_answer(state, question_index, payload=None):
#     """
#     Updates the RFP DataFrame with answer for the selected question.
#     Shows loading message and adds delay before update.
    
#     :param state: Application state dictionary
#     :param question_index: Index of the question to answer (0-4) 
#     :param payload: Optional payload data from the event
#     """
#     try:
#         print(f"Received payload: {payload}")
#         print(f"Initial question_index: {question_index}")
        
#         # Extract record_index from question_index if it's a dict
#         if isinstance(question_index, dict) and 'record_index' in question_index:
#             question_index = question_index['record_index']
#             print(f"Index from record_index: {question_index}")
#         # Extract index from payload if present
#         elif isinstance(payload, dict) and 'index' in payload:
#             question_index = payload['index']
#             print(f"Index from payload dict: {question_index}")
            
#         # Ensure we have a valid integer index
#         if question_index is None:
#             raise ValueError("No valid question index provided in payload or arguments")
            
#         # Convert question_index to int
#         try:
#             question_index = int(question_index)
#             print(f"Converted question_index to int: {question_index}")
#         except (ValueError, TypeError) as e:
#             raise ValueError(f"Could not convert question_index to integer: {e}")
        
#         # Validate index is within bounds
#         if question_index < 0 or question_index >= len(rfp_df):
#             raise ValueError(f"Question index {question_index} is out of bounds")
            
#         print(f"Processing question index: {question_index}")

#         # Update state to show searching message
#         state["message_status"] = "%Searching through knowledge sources..."
#         time.sleep(2)
        
#         # Update state to show generating message
#         state["message_status"] = "%Generating comprehensive answer..."
#         time.sleep(2)
        
#         # Generate answer object for selected question
#         answer_obj = generate_answer_object(question_index)
        
#         # Update DataFrame for selected question
#         rfp_df.at[question_index, 'Answer'] = answer_obj["answer"]
#         rfp_df.at[question_index, 'Notes'] = f"Sources: {', '.join(answer_obj['sources'])}"
#         rfp_df.at[question_index, 'Approved'] = False
        
#         # Store answer object and updated DataFrame in state
#         state["answer_object"] = answer_obj
#         state["rfp_df"] = rfp_df
        
#         # Update state with success message
#         state["message_status"] = "+Answer generated successfully!"
#         print(f"Successfully updated answer for question {question_index}")
        
#     except Exception as e:
#         print(f"Error updating RFP answer: {e}")
#         state["message_status"] = f"-Error generating answer: {str(e)}"
#         state["answer_object"] = {"error": str(e)}

def update_rfp_answer_answered(state):
    time.sleep(2)
    state["rfp_df"] = rfp_df_answered

# Initialize the application state
state = wf.init_state({
    "my_app": {"title": "AI Workflow"},
    "accounts": {},  # Preloaded accounts
    "selected_account_id": None,  # Tracks the ID of the selected account
    # "base_url": base_url,  # Set Base URL in the state
    "account_name": "",  # Name of the selected account
    "account_api_url": "",  # API URL for fetching account data
    "account_search_api_url": "",  # API URL for searching news
    "sf_account_data": "",  # Data for the selected account
    # "kg_api_url": f"{base_url}/kg-question",  # URL for Knowledge Graph API
    # "create_canvas_url": f"{base_url}/create-account-briefing",  # URL for creating a Salesforce Canvas app
    "kg_data": "",  # Data from the Knowledge Graph API
    "combined_account_data": "",  # Combined data from Salesforce and Knowledge Graph
    "executive_summary": "",  # Executive summary of the combined data
    # "writer_abm_app_id": writer_abm_app_id,  # Writer app ID for ABM content
    # "writer_sales_summary_app_id": writer_sales_summary_app_id,  # Writer app ID for Sales Summary content
    # "transcript_graph_id": transcript_graph_id,  # Graph ID for the transcript
    # "transcript_url": f"{base_url}/api/v1/writer/question-graph",  # URL for the transcript
    "abm_content": "",  # ABM content generated by Writer
    "input_content_brief": "Explore the impact of technology on modern communication",
    "input_brand_tone": "Professional",
    "input_target_audience": "Tech Enthusiasts",
    "input_key_message": "Innovation is the key to success in the modern business landscape",
    "output_article_text": "",
    "firefly_instructions": "",
    # "firefly_api_url": f"{base_url}/api/v1/firefly/generate-image",
    "output_firefly_image": "",
    "rfp_df": rfp_df.assign(Answer='', Notes=''),  # Initialize DataFrame with empty answers and notes
    "answer_object": "",
    "message_status": "",  # Status message for RFP answer generation,
    "rfp_table_style": "rfp_table",  # Custom stylesheet name
    "rfp_exec":"UHG is pleased to submit this proposal to provide comprehensive health provider services for Trader Joe’s employees. With our extensive experience in healthcare management, technology-driven solutions, and nationwide provider network, we are uniquely positioned to meet the needs of Trader Joe’s diverse workforce. Our proposal outlines a strategic approach to delivering cost-effective, employee-centric, and innovative healthcare solutions that align with Trader Joe’s values.",
    "rfp_solution":"Our proposed healthcare solution offers a comprehensive suite of benefits designed to support Trader Joe’s diverse workforce at every stage of their health journey. Our customizable health plans include flexible medical, dental, and vision coverage options, allowing employees to select the coverage that best fits their needs—whether they are full-time, part-time, or seasonal staff. In addition to physical health coverage, we prioritize behavioral health support by providing access to confidential counseling, therapy sessions, and immediate crisis assistance, ensuring employees have resources to manage stress, anxiety, and other mental health challenges. Preventive care is at the core of our offering, with regular check-ups, age-appropriate screenings, vaccinations, and proactive early detection programs to help catch potential health issues before they become costly problems. To enhance convenience and accessibility, our telemedicine services provide 24/7 virtual access to primary care physicians and specialists, enabling employees to receive timely care from the comfort of their homes. Our wellness programs go beyond traditional healthcare by offering personalized nutrition guidance, fitness challenges, and chronic disease management tools that promote healthier lifestyles and long-term well-being. Additionally, our Employee Assistance Programs (EAPs) provide holistic support, including financial counseling, legal guidance, and mental and emotional health resources, ensuring that employees and their families receive well-rounded care that supports both their personal and professional lives.",
    "rfp_understanding": "We recognize that Trader Joe’s, as a leading grocery chain with a diverse workforce of 50,000 employees across the United States—including full-time, part-time, and seasonal staff—requires a healthcare provider that aligns with your focus on cost-efficiency, employee satisfaction, and wellness innovation. Our proposed solution is designed to offer high-quality, affordable healthcare options tailored to different employment categories, while also providing innovative wellness programs that enhance employee engagement. Additionally, we ensure seamless access to telemedicine and preventive care solutions, making it easier for employees to manage their health. By leveraging data-driven insights, we help improve workforce health outcomes and deliver measurable improvements in both employee health and overall satisfaction.",
})

# Import the custom stylesheet
state.import_stylesheet("rfp_table", "/static/rfp_table.css?6")