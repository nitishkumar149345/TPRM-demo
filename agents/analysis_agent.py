import json
from typing import Any, Dict

from dotenv import load_dotenv
# from langchain.chat_models import ChatOpenAI
# from langchain.prompts import PromptTemplate
from langchain.schema import HumanMessage, SystemMessage
from langgraph.graph import StateGraph

from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate


load_dotenv()
# Sample Input JSON (Replace with actual JSON input)
sla_data = {
  "vendors": [
    {
      "frequency": "Monthly",
      "time_period":"April/Apr",
      "name": "Vendor A",
      "target_metrics": {
        "uptime_guarantee": "99.9%",
        "support_response_time": "2 hours",
        "penalty_for_downtime": "15% service credit per 30 min",
        "maintenance_window": "Sunday 2 AM - 4 AM",
        "data_backup_frequency": "Daily",
        "disaster_recovery_time": "24 hours"
      },
      "actual_metrics": {
        "uptime": "99.85%",
        "average_support_response_time": "2.5 hours",
        "downtime_in_month": "1 hour",
        "last_backup": "12 hours ago",
        "last_recovery_test": "28 hours"
      },
      
    # },
    # {
    #   "frequency": "Monthly",
    #   "time_period":"April/Apr",
    #   "name": "Vendor B",
    #   "target_metrics": {
    #     "uptime_guarantee": "99.95%",
    #     "support_response_time": "1 hour",
    #     "penalty_for_downtime": "10% service credit if below 99.95%",
    #     "maintenance_window": "Saturday 1 AM - 3 AM",
    #     "data_backup_frequency": "Every 6 hours",
    #     "disaster_recovery_time": "12 hours"
    #   },
    #   "actual_metrics": {
    #     "uptime": "99.97%",
    #     "average_support_response_time": "45 minutes",
    #     "downtime_in_month": "15 minutes",
    #     "last_backup": "4 hours ago",
    #     "last_recovery_test": "10 hours"
    #   },
      
    # },
    # {
    #   "frequency": "Monthly",
    #   "time_period":"April/Apr",
    #   "name": "Vendor C",
    #   "target_metrics": {
    #     "uptime_guarantee": "99.8%",
    #     "support_response_time": "4 hours",
    #     "penalty_for_downtime": "2% service credit per hour",
    #     "maintenance_window": "Wednesday 12 AM - 2 AM",
    #     "data_backup_frequency": "Weekly",
    #     "disaster_recovery_time": "48 hours"
    #   },
    #   "actual_metrics": {
    #     "uptime": "99.6%",
    #     "average_support_response_time": "5 hours",
    #     "downtime_in_month": "5 hours",
    #     "last_backup": "6 days ago",
    #     "last_recovery_test": "55 hours"
    #   },
       
    }
  ]
}

# Define the state to store insights
class SLAState:
    def __init__(self, sla_data: Dict[str, Any]):
        self.sla_data = sla_data
        self.reports = []

# Initialize the LLM model
llm = ChatOpenAI(model_name="gpt-4", temperature=0)

# Define the prompt template
sla_prompt = PromptTemplate(
    input_variables=["vendor_name", "target_metrics", "actual_metrics", "penalties"],
    template="""
    Given the following SLA information for {vendor_name}:
    
    Target SLA:
    {target_metrics}
    
    Actual Performance:
    {actual_metrics}
    
    Penalties Applied:
    {penalties}
    
    Please analyze the differences, identify breaches, calculate penalties, and generate a detailed SLA performance report.
    """
)

sla_report_prompt = PromptTemplate(
    input_variables=["metrics", "reports"],
    template="""
    Given the following SLA information for vendors as json:
    
    Read target and actual metrics of vendors asfrom the json below:
    {metrics}
    
    Reports of Vendors:
    {reports}
    
    Please analyze the SLA performance report and generate a json. For each actual metric add a boolean flag whether it is breached or not.
    if any metric is breached, get relevant penalities from target metrics and calculate penalities for the breached metrics.
    Add calculated penalities against actual metric. Keep taget metrics as it is. 
    If penalty information is not available in target metrics, add 0.
    """
) 
 
# Function to compare SLA metrics using LLM
def compare_sla(state: SLAState):
    for vendor in state.sla_data["vendors"]:
        response = llm([
            SystemMessage(content="You are an expert SLA evaluator. You have to analyze the SLA performance report and generate a detailed SLA performance report."),
            HumanMessage(content=sla_prompt.format(
                vendor_name=vendor["name"],
                target_metrics=json.dumps(vendor["target_metrics"], indent=2),
                actual_metrics=json.dumps(vendor["actual_metrics"], indent=2),
                penalties=json.dumps(vendor.get("penalties", {}), indent=2)
            ))
        ])
        # Write report to a text file
        with open(f"{vendor['name'].replace(' ', '_')}_SLA_Report.txt", "w") as file:
            file.write(response.content)
        
        state.reports.append(f"\nSLA Report for {vendor['name']}:\n{response.content}\n")
    return state

# Function to generate a final SLA report
def generate_report(state: SLAState):
    # Write report to a text file

    response = llm([
            SystemMessage(content="You are an expert SLA evaluator. You have to analyze the SLA performance report and generate a detailed SLA performance report."),
            HumanMessage(content=sla_report_prompt.format(
                metrics=json.dumps(sla_data, indent=2),
                reports=json.dumps(state.reports, indent=2)
            ))
        ])
    with open("Final_SLA_Report.txt", "w") as file:
        file.write(response.content)
    
    return response.content

# Create LangGraph workflow
graph = StateGraph(SLAState({}))
graph.add_node("compare_sla", compare_sla)
graph.add_node("generate_report", generate_report)

graph.set_entry_point("compare_sla")
graph.add_edge("compare_sla", "generate_report")

graph = graph.compile()

# Run the agent
state = SLAState(sla_data)
final_report = graph.invoke(state)
print(final_report)

