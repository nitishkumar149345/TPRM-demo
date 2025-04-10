from enum import Enum
from typing import Union, Optional
from pydantic import BaseModel, Field


class MetadataValue(BaseModel):
    name: str = Field(..., description="The name or label of the metadata field (e.g., 'contract_name', 'vendor_name').")
    value: str = Field(
        None,
        description="The actual value corresponding to the field name. This could be a string (e.g., names, types) or a date (e.g., effective_date, expiration_date)."
    )


class ContractMetadata(BaseModel):

    contract_name: MetadataValue = Field(..., description="Name or title of the contract")
    contract_type: MetadataValue = Field(..., description="Type of contract, e.g., SLA, MSA, NDA")
    vendor_name: MetadataValue = Field(..., description="Name of the vendor involved in the contract")
    customer_name: MetadataValue = Field(None, description="Name of the customer or client")
    effective_date: MetadataValue = Field(..., description="Date when the contract becomes effective")
    expiration_date: MetadataValue = Field(None, description="Date when the contract expires")
    renewal_terms: MetadataValue = Field(None, description="Details about renewal terms if any")
    governing_law: MetadataValue = Field(None, description="Jurisdiction or governing law of the contract")
    # created_by: Optional[str] = Field(None, description="User who created the contract metadata entry")
    # last_modified: Optional[date] = Field(None, description="Date when the contract was last modified")




class ConditionType(str, Enum):
    GREATER_THAN_OR_EQUAL = ">= greater than or equals to"
    GREATER_THAN = "> greater than"
    LESS_THAN_OR_EQUAL = "<= less than or equals to"
    LESS_THAN = "< less than"
    EQUAL = "= equal"
    NOT_EQUAL = "!= not equal"
    WITHIN_RANGE = "within_range"
    OUTSIDE_RANGE = "outside_range"
    PERCENTAGE_DIFFERENCE_LESS_THAN = "%_diff_lt"
    PERCENTAGE_DIFFERENCE_GREATER_THAN = "%_diff_gt"
    ABSOLUTE_DIFFERENCE_LESS_THAN = "abs_diff_lt"
    ABSOLUTE_DIFFERENCE_GREATER_THAN = "abs_diff_gt"


class RemarkType(str, Enum):
    CONSTANT = "constant"
    INCREASING = "increasing"
    DECREASING = "decreasing"


class MetricValue(BaseModel):

    max_value: Union[int, float] = Field(None, description="Max value or threshold of the metric, None if not found")
    min_value: Union[int, float] = Field(None, description="Min value or threshold of the metric, None if not found")
    data_type: str = Field(..., description="Data type of the maximum and minimum values, e.g., (int, %, min, sec)")


class Metric(BaseModel):

    # name: str = Field(..., description="Name of the metric")
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


class MetricComparisonResult(BaseModel):
    is_compliant: bool = Field(..., description="True if actual value meets the condition; False otherwise")
    remark: RemarkType = Field(..., description="Trend of performance compared to target")
    reason: Optional[str] = Field(None, description="Explanation of failure, if not compliant")


class MetricValidationResult(BaseModel):
    is_valid: bool = Field(..., description="True if the comparison logic was correct; False if it was flawed")
    corrected_result: Optional[MetricComparisonResult] = Field(
        None,
        description="Corrected result if original comparison was incorrect"
    )
    notes: str = Field(..., description="Validation explanation or reasoning")
