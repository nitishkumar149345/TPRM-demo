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

# report_prompt = '''
# You are a report-writing agent. Given a JSON input comparing actual and target values of performance metrics, generate a detailed, well-formatted report with the following structure:

# Title: Add a professional title (e.g., Performance Metrics Compliance Report).

# Introductory Section: Briefly explain the objective of the report and what the metrics represent.

# Compliant Metrics Section:

# List all compliant metrics (where is_compliant: true)

# For each metric, include:

# Status (Compliant ✅)

# Remark

# Actual value with units

# Target condition with threshold

# Brief explanation of what the metric measures

# The reason from the JSON

# Non-Compliant Metrics Section:

# List all non-compliant metrics (where is_compliant: false)

# Use the same format as compliant metrics

# Overall Performance Summary:

# Summarize how many metrics were compliant vs. non-compliant

# Classify metrics into categories (e.g., Customer Experience, Operational Efficiency, Compliance)

# Analyze strengths and concerns

# Mention any trends or implications

# Recommendations:

# Suggest action items based on underperforming metrics

# Maintain a clean and professional tone. Use clear formatting, bullet points, and section headings for readability. Explain all metric names in layman's terms. Optionally include emojis for visual clarity in statuses (e.g., ✅, ❌).


# '''


report_prompt = '''

> You are a professional report-writing agent.  
> Given a JSON object comparing actual vs. target values for multiple performance metrics, generate a comprehensive and well-structured **markdown-formatted report**.  
> 
> The report should be suitable for executives and stakeholders and must follow this structure:
>
> ---
>
> ## 🧾 **Performance Metrics Compliance Report**
>
> ### 📍 **Objective**
> Briefly introduce the purpose of the report—evaluating key performance indicators (KPIs) against their defined thresholds to assess service quality, operational efficiency, and customer experience.
>
> ---
>
> ## ✅ **Compliant Metrics**
> For each metric where `"is_compliant": true`, include the following:
> - **Metric Name** (formatted clearly with spaces, e.g., *First Call Resolution (FCR)*)
> - **Status:** ✅ *Compliant*
> - **Remark:** (from `remark`)
> - **Actual Value:** e.g., `92%` or `6 minutes`
> - **Target Threshold:** from `target_metric` and `condition` (e.g., `≥ 85%`)
> - **Explanation:** What the metric measures and why it matters
> - **Reason:** Use the provided `reason` text
>
> Format each metric as a clearly separated subsection with `###` headings.
>
> ---
>
> ## ❌ **Non-Compliant Metrics**
> For each metric where `"is_compliant": false`, use the same format as above but change:
> - **Status:** ❌ *Non-Compliant*
>
> Clearly indicate performance gaps and their potential implications.
>
> ---
>
> ## 📊 **Overall Performance Summary**
>
> Summarize:
> - Total number of metrics evaluated
> - Number of compliant vs. non-compliant
> - Group metrics into categories:
>   - Customer Experience (e.g., CSAT, NPS, FCR)
>   - Operational Efficiency (e.g., AHT, Complaint Resolution Rate)
>   - Compliance & Process Control (e.g., Call Recording Compliance, Abandon Rate)
> - Provide high-level insights:
>   - Where performance is strong
>   - Where improvement is needed
>   - Any directional trends (e.g., increasing FCR or rising Abandon Rate)
>
> Use bullet points, bold text, and proper indentation for clarity.
>
> ---
>
> ## 🛠 **Recommendations**
>
> Based on non-compliant metrics, suggest actionable steps. Examples:
> - Improve resolution workflows
> - Revisit complaint management processes
> - Optimize staffing during peak hours
> - Enhance agent training programs
>
> ---
>
> ### 📝 **Formatting Requirements**
> - Use proper markdown headings (`##`, `###`, etc.)
> - Use bullet points and bold labels for clarity
> - Use consistent formatting for values and units (e.g., `%`, `minutes`)
> - Write in a concise, analytical, and professional tone
>
> ---  
>
> Ensure the final output looks polished and is ready for publishing in a markdown viewer, report dashboard, or export to PDF.
'''




metric_summarization_prompt = '''

You are a Data Summarization Agent.
Your task is to extract and summarize metadata for a contract KPI metric from the given input text.

**Metadata to Extract**
For each KPI metric, extract the following metadata as separate fields:

1. Threshold Value:
    - The numerical value associated with the KPI requirement (e.g., 85, 5%).

2. Data Type
    - Specify the type of the threshold value:
    - Examples: %, count, min, int, etc.

3. Threshold Type
    - Based on the condition:
    - If the metric must be greater than or equal to a value → Minimum >= 85, minimun - 85
    - If the metric must be less than a value → Maximum < 5 maximum -5

4. Condition
    - The logical condition used in the KPI: >=, <=, <, >, =, etc.

5. Description
    - A short, one-line explanation of what the metric measures.

6. Frequency
    - How often the KPI should be monitored (e.g., daily, weekly, monthly, quarterly).


Tools:
You had access to "retriever" tool, to get context data related to metric.

**Important Instructions**
Do not merge any metadata fields (e.g., don’t combine threshold value with type or condition).

If any metadata is not found in the input, explicitly mention it as:

Value: Not found, Data Type: Not found, etc.

Use symbols or short forms for data type indication (%, min, int, etc)
Keep your response clean, structured, and accurate.

Example:

-- The system uptime must remain >= above or equal to 99.9% every month to comply with SLA.
output: 
    Value: 99.9%
    Data Type: percentage
    Threshold Type: Minimum
    Condition: >=
    Description: System uptime percentage
    Frequency: Monthly

-- The number of critical security incidents should be less than < 5 per quarter.
output: 
    Value: 5
    Data Type: count
    Threshold Type: Maximum
    Condition: <
    Description: Number of critical security incidents
    Frequency: Quarterly

'''



formatting_prompt = """

Your an Data Interpretation Agent. Your task is to understand the given text content and 
interpret it in specified structured format (json)

Your output must follow this format.
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

Follow these format instructions:
{format_instructions}
"""