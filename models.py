from pydantic import BaseModel, Field
from typing import List, Annotated, Literal
from fastapi import UploadFile


class Extract(BaseModel):

    parties: Annotated[List[str], Field(..., description="The individuals or entities entering into the contract")]
    effective_date: Annotated[str, Field(..., description="The date when the contract becomes legally binding and enforceable")]
    term: Annotated[str, Field(..., description="The period during which the contract is in effect")]
    governing_law: Annotated[str, Field(..., description="The jurisdiction whose laws will interpret and enforce the contract")]
    payment_terms: Annotated[str, Field(..., description="Specifies when, how, and how much payment will be made")]
    termination: Annotated[str, Field(..., description="The conditions under which the contract can be ended before its natural expiration")]
    auto_renewal: Annotated[str, Field(..., description="A clause that automatically extends the contract for additional periods unless one party gives notice.")]
    confidentiality: Annotated[str, Field(..., description="Obligation to protect sensitive information shared during the contract")]
    indemnity: Annotated[str, Field(..., description="Promise to compensate the other party for losses arising from certain events")]
    liability_cap: Annotated[str, Field(..., description="Maximum amount one party can recover from the other for breaches, provide number with currency")]
    signatories: Annotated[List[str], Field(..., description="Individuals authorized to bind the parties to the contract")]
            

class RAGData(BaseModel):

    output: str
    citations: List[str]


class AskRequest(BaseModel):
    """Request body for /ask endpoint"""

    query: str
    rag_data: RAGData

class RiskyClause(BaseModel):
    finding: Annotated[str, Field(description="Your simplified explanation of the detected risky clause.")]
    severity: Annotated[Literal["Low", "Medium", "High", "Critical"], Field(description="Severity level of the detected risk.")]
    evidence: Annotated[str, Field(description="The detected clause in consideration, pasted as it is given in the contract.")]

class Audit(BaseModel):

    risks: List[RiskyClause]