# MCP Secure Tool Gateway

## Overview

This project implements a secure MCP gateway for Odoo ERP.

Features:
- JWT Authentication
- Role-Based Access Control (RBAC)
- Secure MCP Tools
- FastAPI Gateway
- Dynamic Tool Routing

Architecture:

Client → FastAPI Gateway → Security Layer → MCP Tools → Odoo ERP

---

## Setup

### 1 Install dependencies

pip install -r requirements.txt

### 2 Configure environment

Create .env file based on .env.example

### 3 Start Odoo

docker start odoo
docker start db

### 4 Run MCP Server

python -m mcp_odoo.server

### 5 Run Gateway

uvicorn gateway.main:app --reload

---

## API

Swagger documentation:

http://127.0.0.1:8000/docs

---

## Authentication

POST /login

Example:

{
 "username": "admin",
 "password": "admin123"
}

---

## Tool Execution

POST /tool/{tool_name}

Example:

POST /tool/get_partner

{
 "token": "<JWT>",
 "params": {
   "name": "Azure"
 }
}