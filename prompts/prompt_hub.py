base_schema = """
    Format the extracted information as a JSON object with this structure:
    ```json
    {{
      "name": "{field_name}",
      "value": "<extracted value>"
    }}
    ```
    
    Rules:
    1. For date fields, use YYYY-MM-DD format
    2. For text fields, extract the most relevant value
    3. If no value found, set "value" to null
    4. Do not include explanations or additional text
"""


metric_schema = """
    Format the metric information as a JSON object with this structure:
    ```json
    {{
        "metric_value": {{
            "min_value": "<numeric value or null>",
            "max_value": "<numeric value>",
            "data_type": "<unit type>"
        }},
        "condition": "<comparison operator>",
        "frequency": "<evaluation period>",
        "description": "<metric purpose>"
    }}
    ```
"""


metric_field_instructions = """

Formulate a focused query based on the input {field_name} to retrieve all content that could mention the relevant metric and its associated thresholds, conditions, frequency, or description.
Example query format: 'Information related to [field_name] metric, including threshold values, evaluation frequency, and description'

Use custom_retriever with this query to extract the most relevant chunks from the contract.

Analyze the retrieved content carefully to extract the following details:
min_value — Set if value is like ≥ to X, or if a range is provided, should contain only numerical value, int, float.
max_value — Set if value is like ≤ to Y, or if a range is provided. should contain only numerical value, int, float.
Condition — The condition or scenario under which the metric is applicable or monitored, (>= grater than equals to, <= less than equal to, = equal to, etc..)
            You might get the condition near value. 
frequency — How frequently the metric is evaluated, (daily, weekly, monthly, quaterly, yearly, etc.)
description — A one-line explanation of what the metric measures.
output: 
Output must be summary of the given context covering all mentioned fields.

"""


base_field_instructions = '''

    Steps:
    1. Formulate a focused query for {field_name} to retrieve all content that could mention the relevant answer for field.
    2. Use custom_retriever with this query to extract the most relevant chunks from the contract.
    3. Analyze context to find the most relevant value
    Query Examples:
    - For contract_name: "What is the name or title of this contract?"
    - For effective_date: "When does this contract become effective?"
    - For vendor_name: "Who is the service provider/vendor in this contract?"

    Note: Extract only the most relevant value, avoiding explanations or context.

'''
