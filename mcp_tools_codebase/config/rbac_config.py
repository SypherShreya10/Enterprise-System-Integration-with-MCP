TOOL_PERMISSIONS = {

# ---------------------------
# Identity / Core tools
# ---------------------------

"get_partner": ["viewer", "operator", "sales_agent", "manager", "admin"],

"create_partner": ["operator", "sales_agent", "manager", "admin"],

"get_user": ["manager", "admin"],

"get_company": ["viewer", "operator", "sales_agent", "manager", "admin"],


# ---------------------------
# HR tools
# ---------------------------

"get_employee": ["viewer", "operator", "manager", "admin"],

"get_department": ["viewer", "operator", "manager", "admin"],

"get_job": ["viewer", "operator", "manager", "admin"],

"get_employee_leaves": ["operator", "manager", "admin"],

"check_employee_availability": ["operator", "manager", "admin"],

"get_employee_attendance": ["operator", "manager", "admin"],


# ---------------------------
# CRM tools
# ---------------------------

"get_lead": ["viewer", "operator", "sales_agent", "manager", "admin"],

"update_lead_stage": ["sales_agent", "manager", "admin"],

"get_stage": ["viewer", "operator", "sales_agent", "manager", "admin"],

"get_team": ["viewer", "operator", "sales_agent", "manager", "admin"],

"create_activity": ["operator", "sales_agent", "manager", "admin"],

"get_activity": ["viewer", "operator", "sales_agent", "manager", "admin"],
}




# TOOL_PERMISSIONS = {

#     # Identity tools
#     "get_partner": ["viewer","operator","sales_agent","manager","admin"],
#     "create_partner": ["operator","sales_agent"],
#     "get_user": ["manager","admin"],
#     "get_company": ["viewer","operator","sales_agent","manager","admin"],

#     # HR tools
#     "get_employee": ["viewer","operator","sales_agent","manager","admin"],
#     "get_department": ["viewer","operator","sales_agent","manager","admin"],
#     "get_job": ["viewer","operator","sales_agent","manager","admin"],
#     "get_employee_leaves": ["operator","manager"],
#     "check_employee_availability": ["operator","manager"],
#     "get_employee_attendance": ["manager","admin"],

#     # CRM tools
#     "get_lead": ["viewer","operator","sales_agent","manager","admin"],
#     "update_lead_stage": ["manager"],
#     "get_stage": ["viewer","operator","sales_agent","manager","admin"],
#     "get_team": ["viewer","operator","sales_agent","manager","admin"],
#     "create_activity": ["operator","sales_agent"],
#     "get_activity": ["viewer","operator","sales_agent","manager","admin"],
# }


