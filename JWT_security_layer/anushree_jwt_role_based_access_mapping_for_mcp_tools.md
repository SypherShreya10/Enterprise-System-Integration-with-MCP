# JWT Role-Based Access Mapping for MCP Tools

## Purpose
This document defines **future-ready JWT role-based access control (RBAC)** for all MCP tools, derived strictly from:
- AI Safety & Execution Constraints
- Infrastructure notes
- Phase 1 & Phase 2 business object maps
- MCP Tool List (35 tools)

This document answers one question:
> **Which JWT role is allowed to call which MCP tool (and why)?**

This is a **design + security reference**, not implementation code.

---

## JWT Roles (Defined at MCP Level)

These are **JWT roles**, not Odoo roles.

### 1. `viewer`
- Read-only
- Lowest privilege
- Default role

### 2. `operator`
- Can create low-risk business records
- No authority changes

### 3. `sales_agent`
- Sales workflow execution (draft-level only)

### 4. `manager`
- Can move business state forward (controlled updates)

### 5. `admin`
- Supervisory visibility
- NO raw power escalation

> ⚠️ No JWT role ever maps directly to `res.users` or `res.groups`

---

## GLOBAL RULES (Apply to ALL Tools)
- JWT REQUIRED: ✅ YES (all tools)
- Company scope enforced
- Max 100 records
- No delete operations
- All actions logged

---

## SECTION 1: Identity & Access Management (Tools 001–004)

| Tool ID | Tool Name        | JWT Roles Allowed | Reason |
|-------|------------------|------------------|--------|
| 001 | get_partner | viewer, operator, sales_agent, manager, admin | Foundational identity lookup |
| 002 | create_partner | operator, sales_agent | Medium risk create, no authority |
| 003 | get_user | manager, admin | Audit / assignment only |
| 004 | get_company | viewer+ | Context only |

---

## SECTION 2: HR / Employee Management (Tools 005–010)

| Tool ID | Tool Name | JWT Roles Allowed | Reason |
|-------|-----------|------------------|--------|
| 005 | get_employee | viewer+ | Org context, read-only |
| 006 | get_department | viewer+ | Structure context |
| 007 | get_job | viewer+ | Reference data |
| 008 | get_employee_leaves | operator, manager | Planning-sensitive |
| 009 | check_employee_availability | operator, manager | Resource planning |
| 010 | get_employee_attendance | manager, admin | Workforce visibility |

---

## SECTION 3: CRM / Sales Pipeline (Tools 011–016)

| Tool ID | Tool Name | JWT Roles Allowed | Reason |
|-------|-----------|------------------|--------|
| 011 | get_lead | viewer+ | Sales visibility |
| 012 | update_lead_stage | manager ONLY | High-risk state change |
| 013 | get_stage | viewer+ | Reference |
| 014 | get_team | viewer+ | Reporting |
| 015 | create_activity | operator, sales_agent | Workflow automation |
| 016 | get_activity | viewer+ | Task tracking |

---

## SECTION 4: Inventory / Stock (Tools 017–020)

| Tool ID | Tool Name | JWT Roles Allowed | Reason |
|-------|-----------|------------------|--------|
| 017 | get_product | viewer+ | Fundamental read |
| 018 | get_product_stock | viewer+ | Inventory visibility |
| 019 | check_product_availability | operator, sales_agent | Fulfillment planning |
| 020 | get_stock_location | viewer+ | Context |

---

## SECTION 5: Sales Orders (Tools 021–024)

| Tool ID | Tool Name | JWT Roles Allowed | Reason |
|-------|-----------|------------------|--------|
| 021 | get_sale_order | viewer+ | Order tracking |
| 022 | get_sale_order_lines | viewer+ | Order analysis |
| 023 | create_sale_order | sales_agent | Draft-only creation |
| 024 | get_customer_order_history | operator, sales_agent, manager | Relationship context |

---

## SECTION 6: Purchasing (Tools 025–027)

| Tool ID | Tool Name | JWT Roles Allowed | Reason |
|-------|-----------|------------------|--------|
| 025 | get_purchase_order | viewer+ | Incoming materials |
| 026 | get_purchase_order_lines | viewer+ | Procurement visibility |
| 027 | check_material_availability | manager | Manufacturing gating |

---

## SECTION 7: Manufacturing (Tools 028–030)

| Tool ID | Tool Name | JWT Roles Allowed | Reason |
|-------|-----------|------------------|--------|
| 028 | get_manufacturing_order | viewer+ | Production visibility |
| 029 | check_manufacturing_capacity | manager | Scheduling authority |
| 030 | get_bill_of_materials | viewer+ | Planning context |

---

## SECTION 8: Accounting / Finance (Tools 031–033)

| Tool ID | Tool Name | JWT Roles Allowed | Reason |
|-------|-----------|------------------|--------|
| 031 | get_customer_invoices | manager, admin | Financial sensitivity |
| 032 | check_customer_credit | manager | Credit gating |
| 033 | get_payment_history | manager, admin | Risk analysis |

---

## SECTION 9: Composite / Cross-Domain (Tools 034–035)

| Tool ID | Tool Name | JWT Roles Allowed | Reason |
|-------|-----------|------------------|--------|
| 034 | check_order_fulfillment_feasibility | manager | High-impact decision |
| 035 | analyze_customer_relationship | manager, admin | Strategic analysis |

---

## FINAL NOTES
- JWT Level 1: only **authentication required** (no role enforcement)
- JWT Level 2: role-based enforcement using THIS document
- Odoo roles remain unchanged
- MCP is the sole enforcement point

> This document is the **RBAC contract** for future JWT integration.

