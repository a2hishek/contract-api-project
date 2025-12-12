from langchain.chat_models import init_chat_model
from langchain.messages import ToolMessage, AIMessage, SystemMessage, HumanMessage
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.prompts import ChatPromptTemplate
from langchain.agents import create_agent
from prompts import rag_prompt, llm_prompt
from rag import retrieve_context
from models import Extract, Audit
from dotenv import load_dotenv
import base64
import os
load_dotenv()

model = init_chat_model("google_genai:gemini-2.5-flash-lite")

model_with_structured_output = model.with_structured_output(Extract)

model_for_audit = model.with_structured_output(Audit)


def pdf_to_base64(pdf_path: str) -> str:
    """Convert PDF file to base64 string"""
    with open(pdf_path, 'rb') as f:
        return base64.b64encode(f.read()).decode('utf-8')

def extract_from_pdf(pdf_path: str):
    """
    Extract structured data from PDF using Gemini 2.5 Flash Lite
    
    Args:
        pdf_path: Path to the PDF file to extract from
        
    Returns:
        Extract: Pydantic model with extracted contract information
        
    Raises:
        FileNotFoundError: If PDF file doesn't exist
        Exception: If extraction fails
    """
    
    
    # Validate file exists
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")
    
    try:
        # Convert PDF to base64
        pdf_file = pdf_to_base64(pdf_path)

        # Create message for model
        message = [{
                "role": "system",
                "content": "Act as a legal contract expert and help extract useful information from the document. Extract all relevant contract details accurately."
        },
        {
        "role": "user",
        "content": [
            {"type": "text", "text": "Extract all structured information from this contract document including parties, dates, terms, and all other relevant details."},
            {
                "type": "file",
                "base64": pdf_file,
                "mime_type": "application/pdf",
            },
        ]
        }]
        
        # Invoke model
        result = model_with_structured_output.invoke(message)

        return result
    
    except Exception as e:
        raise Exception(f"Error extracting data from PDF: {str(e)}")


tools = [retrieve_context]
agent = create_agent(model, tools, system_prompt=rag_prompt)

# query = (
#     "Explain what is the contract about?\n\n"
#     "Then, tell Who are the signing parties?"
# )

# for event in agent.stream(
#     {"messages": [{"role": "user", "content": query}]},
#     stream_mode="values",
# ):
#     event["messages"][-1].pretty_print()

def get_citations(output):
    citations = []
    for message in output["messages"]:
        if isinstance(message, ToolMessage):
            for i, document in enumerate(message.artifact):
                citation = f"CITATION {i+1}: \n\n"
                citation += document.page_content
                citation += f"\n\n{'='*30}\n\n"
                citations.append(citation)
                # print(document.page_content)
                # print("\n\n")
    return citations

def perform_rag(query: str):

    output = agent.invoke({"messages": [{"role": "user", "content": query}]})
    final_output = output["messages"][-1].content
    citations = get_citations(output)
    return final_output, citations

def llm_response(query: str, context: dict):
    
    agent_output = context.get("output", "")
    citations = "".join(context.get("citations", []))

    messages = [
        SystemMessage(content=llm_prompt.format(
            agent_output=agent_output,
            citations=citations
        )),
        HumanMessage(content=query)
    ]
    response = model.invoke(messages)

    return response


def llm_response_stream(query: str, context: dict):
    """
    Stream tokens from the LLM using the provided RAG context.
    Yields incremental text chunks.
    """

    agent_output = context.get("output", "")
    citations = "".join(context.get("citations", []))

    messages = [
        SystemMessage(content=llm_prompt.format(
            agent_output=agent_output,
            citations=citations
        )),
        HumanMessage(content=query)
    ]

    # stream partial generations
    for chunk in model.stream(messages):
        content = getattr(chunk, "content", "")
        if content:
            # content may be str or list; coerce to str
            yield content if isinstance(content, str) else str(content)

def llm_audit(pdf_path: str):
    
    # Validate file exists
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")
    
    try:
        # Convert PDF to base64
        pdf_file = pdf_to_base64(pdf_path)

        # Create message for model
        message = [{
                "role": "system",
                "content": "Act as a legal contract expert. Analyse the uploaded contract thoroughly and help find out any risky clauses in the contract."
        },
        {
        "role": "user",
        "content": [
            {"type": "text", "text": "Analyse the document and find out any risky clauses present in the contract"},
            {
                "type": "file",
                "base64": pdf_file,
                "mime_type": "application/pdf",
            },
        ]
        }]
        
        # Invoke model
        result = model_for_audit.invoke(message)

        return result
    
    except Exception as e:
        raise Exception(f"Error extracting data from PDF: {str(e)}")