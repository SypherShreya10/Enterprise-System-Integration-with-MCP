# MCP Secure Tool Gateway

## Overview

This project implements a secure MCP gateway for Odoo ERP.

Features:
- JWT Authentication
- Role-Based Access Control (RBAC)
- Secure MCP Tools
- FastAPI Gateway
- Dynamic Tool Routing

System Architecture:

Client
  ↓
FastAPI Gateway
  ↓
JWT Verification
  ↓
RBAC Permission Check
  ↓
Audit Log Recorded
  ↓
MCP Tool Called
  ↓
Odoo Client (XML-RPC)
  ↓
Odoo ERP Database

Elaborated:

                ┌─────────────────────────────┐
                │           Client             │
                │  (Swagger / Frontend / CLI) │
                └──────────────┬──────────────┘
                               │
                               │ HTTP Requests
                               │
                               ▼
                ┌─────────────────────────────┐
                │        FastAPI Gateway       │
                │        gateway/main.py       │
                │                              │
                │  • Login endpoint            │
                │  • Tool execution endpoint   │
                │  • Tool discovery endpoint   │
                └──────────────┬──────────────┘
                               │
                               │ JWT Token
                               ▼
                ┌─────────────────────────────┐
                │      Authentication Layer    │
                │      auth/jwt_handler.py     │
                │                              │
                │  • JWT token creation        │
                │  • JWT token verification    │
                └──────────────┬──────────────┘
                               │
                               │ Verified User
                               ▼
                ┌─────────────────────────────┐
                │      Authorization Layer     │
                │      security/secure_tool.py │
                │                              │
                │  • RBAC Role validation      │
                │  • Tool permission checks    │
                │  • Security enforcement      │
                └──────────────┬──────────────┘
                               │
                               │
                               ▼
                ┌─────────────────────────────┐
                │        MCP Tool Server       │
                │        mcp_odoo/server.py    │
                │                              │
                │  • Registers all MCP tools   │
                │  • Routes tool calls         │
                └──────────────┬──────────────┘
                               │
                               │ Tool Invocation
                               ▼
                ┌─────────────────────────────┐
                │         Tool Layer           │
                │   mcp_odoo/tools/*.py        │
                │                              │
                │  • CRM tools                 │
                │  • HR tools                  │
                │  • Inventory tools           │
                │  • Sales tools               │
                └──────────────┬──────────────┘
                               │
                               │ XML-RPC
                               ▼
                ┌─────────────────────────────┐
                │        Odoo Client           │
                │     mcp_odoo/odoo_client.py  │
                │                              │
                │  • Odoo authentication       │
                │  • search_read               │
                │  • create / update
                └──────────────┬──────────────┘
                               │
                               │ Database Operations
                               ▼
                ┌─────────────────────────────┐
                │           Odoo ERP           │
                │  Docker Container :8069     │
                │                              │
                │  PostgreSQL Database         │
                └─────────────────────────────┘

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
