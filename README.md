# Enterprise Automation with MCP, LangGraph, and AI Agents

## Overview

This project implements an **AI-driven enterprise automation system** that connects large language models (LLMs) with enterprise systems such as **ERP, CRM, and HR** using the **Model Context Protocol (MCP)**.

The system uses **LangGraph agents** to interpret user requests and execute business operations through enterprise APIs and knowledge systems.

The goal is to enable AI models to **interact safely with enterprise infrastructure**, automate workflows, and retrieve business information.

---

## Architecture

The system follows a **multi-agent orchestration architecture**.

```
User
  │
  ▼
Supervisor Agent
  │
  ▼
Router
 ├─────────────┬─────────────┐
 ▼             ▼             ▼
HR Agent     CRM Agent     ERP Agent
  │             │             │
  ▼             ▼             ▼
Tool Executor (MCP Tools)
  │
  ▼
Enterprise Systems
 ├── ERP / CRM / HR (Odoo APIs)
 ├── NebulaGraph (Business Process Graph)
 └── Weaviate (Enterprise Knowledge Retrieval)
```

### Components

**LangGraph Agents**

* Supervisor Agent: Classifies the domain of the request.
* Router: Routes requests to the appropriate domain agent.
* Domain Agents:

  * HR Agent
  * CRM Agent
  * ERP Agent
* Response Agent: Generates the final response for the user.

**Tool Executor**

* Executes tools registered in the **Tool Registry**.
* Ensures agents interact only with allowed enterprise tools.

**Enterprise Systems**

* ERP / CRM / HR: accessed through MCP tools.
* NebulaGraph: models business relationships and processes.
* Weaviate: retrieves enterprise knowledge using vector search.

---

## Technologies Used

* Python
* LangGraph
* LangChain
* Groq LLM API
* MCP (Model Context Protocol)
* NebulaGraph
* Weaviate
* Odoo (ERP backend)

---

## Project Structure

```
project-root/

ai/
 ├── agents/
 │   ├── supervisor_agent.py
 │   ├── hr_agent.py
 │   ├── crm_agent.py
 │   ├── erp_agent.py
 │   └── response_agent.py
 │
 ├── graph/
 │   ├── builder.py
 │   ├── router.py
 │   └── state.py
 │
 ├── llm/
 │   └── groq_client.py
 │
 └── tools/
     ├── tool_executor.py
     └── tool_registry.py

tools/
 ├── hr.py
 ├── crm.py
 ├── erp.py
 └── mail.py

odoo_client.py
server.py
```

---

## How It Works

1. The user sends a query.
2. The **Supervisor Agent** determines which domain the request belongs to.
3. The **Router** directs the request to the correct domain agent.
4. The **Domain Agent** selects the appropriate enterprise tool.
5. The **Tool Executor** runs the tool via MCP.
6. Data is retrieved from enterprise systems.
7. The **Response Agent** formats the final response.

Example flow:

```
User: "Show employees named John"

Supervisor → HR domain
Router → HR Agent
HR Agent → get_employee tool
Tool Executor → Odoo API
Response Agent → formatted answer
```

---

## Setup Instructions

### 1. Clone the Repository

```
git clone <repository-url>
cd project-folder
```

### 2. Install Dependencies

```
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Create a `.env` file.

```
GROQ_API_KEY=your_groq_api_key

ODOO_URL=http://localhost:8069
ODOO_DB=odoo
ODOO_USERNAME=admin
ODOO_PASSWORD=admin
```

### 4. Run the System

```
python test_graph.py
```

Or run the API server:

```
uvicorn server:app --reload
```

---

## Example Queries

HR:

```
Show employees named John
Check employee attendance
```

CRM:

```
Create a customer named Tesla
Update lead stage
```

ERP:

```
Check stock of laptop
Create a sale order
```

---

## Future Improvements

* Structured tool outputs using Pydantic schemas
* Enhanced error handling and tool validation
* Integration with NebulaGraph for workflow modeling
* Knowledge retrieval using Weaviate
* Authentication and enterprise security policies

---

## Contributors

* AI Agent System Development: LangGraph orchestration and LLM integration
* Enterprise System Integration: MCP tools, NebulaGraph modeling, and Weaviate knowledge retrieval

---

## License

This project is for educational and research purposes.
