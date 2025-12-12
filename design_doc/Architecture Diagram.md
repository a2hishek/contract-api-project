**Architecture Diagram**

![contract_api_diag](https://github.com/user-attachments/assets/a6b60bbc-575c-40d2-afa4-a4a6a5ca9646)


**Data Flow/ Working:**

* The user uploads a pdf file of the contract document through the streamlit interface.  
* The file is sent to the backend using a [requests.post](http://requests.post)() call on the /ingest endpoint, the file is stored in a local directory.  
* After saving the file in the local directory, the file is loaded using a document loader and split into equal length chunks using RecursiveCharacterTextSplitter and is stored as vector embeddings in the ChromaDB vector store using google gemini embedding model.  
* This step completes the setup for performing RAG on the pdf file.  
* After uploading the file, the user can extract the file contents and view them in the extract tab of the UI by calling the /extract endpoint of the server.  
* The file text is passed to the LLM from the local directory to perform extract and audit steps. The LLM uses separate pydantic data models to generate structured output for the extract and audit endpoint request.  
* The user can ask questions through the ask tab in the UI. The query is passed to the backend using the /rag and /ask endpoint.  
* The /rag endpoint is used to retrieve relevant context from the vector store, it uses a agentic loop to retrieve multiple documents to answer the user query. It returns the agent’s insights and relevant citations from the contract.  
* The /ask endpoint is used to get the final response for the user query, it takes the user query and the RAG output and generates a final response to display in the response box of the UI.  
* The user can store multiple files in the vector store, the chromadb collection can be filtered using document metadata to get only the concerned file’s embeddings.

**Data Models:**

* **AskRequest**  
  Key Fields:  
  - query: The user’s query as a string  
  - rag\_data: The RAG step output consists of agent output and list of citations from the document.

* **Audit**  
  Key Fields:  
  - risks: A list of RiskyClause objects which consists of three entities, findings, severity and evidence.

* **Extract**  
  Key Fields  
  - parties  
  - effective\_date   
  - term  
  - governing\_law  
  - payment\_terms  
  - termination  
  - auto\_renewal  
  - confidentiality  
  - indemnity  
  - liability\_cap  
  - signatories
