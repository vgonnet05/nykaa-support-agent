# Import Pydantic tools to define and validate structured responses.
from pydantic import BaseModel, Field


# Define the required structure for a Nykaa customer-support response.
class SupportResponse(BaseModel):

    # The answer that will be shown to the customer.
    answer: str = Field(
        description="Answer to the customer's question"
    )

    # Names of knowledge-base documents supporting the answer.
    source_documents: list[str] = Field(
        description="Knowledge-base documents supporting the answer"
    )

    # Indicates whether the query should be escalated to a human.
    requires_escalation: bool = Field(
        description="Whether the customer query needs human escalation"
    )