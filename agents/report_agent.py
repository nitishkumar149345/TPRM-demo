from constants import keys
from prompts.prompt_hub import report_prompt

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate




prompt = ChatPromptTemplate.from_messages([
    ('system', report_prompt),
    ('user','{input}')
])


model = ChatOpenAI(openai_api_key= keys.OPENAI_API_KEY) 
chain = prompt | model

class ReportWriter:
    def __init__(self, comparison_json: dict):
        self.comparison_json = comparison_json
        self.llm_model = ChatOpenAI(openai_api_key= keys.OPENAI_API_KEY)


    def __call__(self,):
        prompt = ChatPromptTemplate.from_messages([
            ('system', report_prompt),
            ('user','{input}')
        ])

        chain = prompt | self.llm_model

        query = f'From this comparison json: {self.comparison_json}, write an well formatted summary report.'

        response = chain.invoke({"input": query})

        return response
    

if __name__ == '__main__':
    comparison_json ='''{ "first_call_resolution(FCR)": {
      "is_compliant": true,
      "remark": "increasing",
      "reason": "The actual value of 92 % is greater than the target value of 85 %. The condition 92 % >= 85 % is met.",
      "actual_metric": {
        "value": 92,
        "data_type": "%"
      },
      "target_metric": {
        "min_value": null,
        "max_value": 85,
        "data_type": "%"
      },
      "condition": ">= greater than or equals to"
    },
    "average_handel_time(AHT)": {
      "is_compliant": true,
      "remark": "down",
      "reason": "The actual value of 6 minutes is below the target value of 7 minutes.",
      "actual_metric": {
        "value": 6,
        "data_type": "minutes"
      },
      "target_metric": {
        "min_value": null,
        "max_value": 7,
        "data_type": "minutes"
      },
      "condition": "<= less than or equal to"
    },
    "customer_satisfaction(CSAT)": {
      "is_compliant": false,
      "remark": "down",
      "reason": "The actual value of 85 % is below the target value of 90 %. The condition is not satisfied as the actual value is less than the target value.",
      "actual_metric": {
        "value": 85,
        "data_type": "%"
      },
      "target_metric": {
        "min_value": null,
        "max_value": 90,
        "data_type": "%"
      },
      "condition": ">= greater than or equals to"
    },
    "net_promoter_score(NPS)": {
      "is_compliant": true,
      "remark": "increasing",
      "reason": "The actual value of 84 % is greater than the target value of 75 %, meeting the condition of Actual >= Target.",
      "actual_metric": {
        "value": 84,
        "data_type": "%"
      },
      "target_metric": {
        "min_value": null,
        "max_value": 75,
        "data_type": "%"
      },
      "condition": ">= greater than or equals to"
    },
    "abandon_rate": {
      "is_compliant": false,
      "remark": "up",
      "reason": "The condition is not satisfied because 6% is greater than 5%.",
      "actual_metric": {
        "value": 6,
        "data_type": "%"
      },
      "target_metric": {
        "min_value": null,
        "max_value": 5,
        "data_type": "%"
      },
      "condition": "<= less than or equals to"
    },
    "complaint_resolution_rate": {
      "is_compliant": false,
      "remark": "down",
      "reason": "The actual value of 75 % is below the target value of 90 %, hence the condition '>= greater than or equals to' is not satisfied.",
      "actual_metric": {
        "value": 75,
        "data_type": "%"
      },
      "target_metric": {
        "min_value": null,
        "max_value": 90,
        "data_type": "%"
      },
      "condition": ">= greater than or equals to"
    },
    "call_recording _compliance": {
      "is_compliant": true,
      "remark": "increasing",
      "reason": "Actual value of 90% is greater than the target value of 85%, meeting the condition of '>='.",
      "actual_metric": {
        "value": 90,
        "data_type": "%"
      },
      "target_metric": {
        "min_value": null,
        "max_value": 85,
        "data_type": "%"
      },
      "condition": ">="
    }
  }}'''
    
    agent = ReportWriter(comparison_json= comparison_json)
    report = agent()
    with open('report.md','w', encoding='utf-8')as r:
        r.write(report.content)
    from rich import print
    print (report.content)
