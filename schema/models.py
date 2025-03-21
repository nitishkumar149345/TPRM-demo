from enum import Enum
from typing import Union
from pydantic import BaseModel, Field

class ConditionType(str, Enum):
    GREATER_THAN_OR_EQUAL = ">="
    LESS_THAN_OR_EQUAL = "<="
    EQUAL = "="
    NOT_EQUAL = "!="
    NOT_APPLIED = None


class MetricValue(BaseModel):

    max_value: Union[int, float] = Field(None, description="Max value or threshold of the metric, None if not found")
    min_value: Union[int, float] = Field(None, description="Min value or threshold of the metric, None if not found")
    data_type: str = Field(..., description="Data type of the maximum and minimum values, e.g., (int, %, min, sec)")


class Metric(BaseModel):

    name: str = Field(..., description="Name of the metric")
    metric_value: MetricValue = Field(..., description="Maximum and minimum value or numerical threshold of the metric")
    condition: ConditionType = Field(..., description="Condition to follow by the metric")
    frequency: str = Field(..., description="How frequent the metric should be validated")
    description: str = Field(..., description="A one-line description about the metric")


class Metrics(BaseModel):

    first_call_resolution: Metric = Field(..., alias="First Call Resolution (FCR)")
    average_handle_time: Metric = Field(..., alias="Average Handle Time (AHT)")
    customer_satisfaction: Metric = Field(..., alias="Customer Satisfaction (CSAT)")
    net_promoter_score: Metric = Field(..., alias="Net Promoter Score (NPS)")
    abandon_rate: Metric = Field(..., alias="Abandon Rate")
    complaint_resolution_rate: Metric = Field(..., alias="Complaint Resolution Rate")
    pii_handling_compliance: Metric = Field(..., alias="PII Handling Compliance")
    data_access_controls: Metric = Field(..., alias="Data Access Controls")
    data_breach_incidents: Metric = Field(..., alias="Data Breach Incidents")
    staff_training_completion: Metric = Field(..., alias="Staff Training Completion")
    secure_data_access: Metric = Field(..., alias="Secure Data Access")
    regulatory_compliance_audits: Metric = Field(..., alias="Regulatory Compliance Audits")
    regulatory_complaint_responses: Metric = Field(..., alias="Regulatory Complaint Responses")
    call_recording_compliance: Metric = Field(..., alias="Call Recording Compliance")
