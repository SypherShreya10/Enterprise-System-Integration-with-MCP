from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from fastapi.security import OAuth2PasswordRequestForm
from Auth import authenticate_user, create_access_token, verify_token
from routers import hr_tools
from auth.dependencies import get_current_user



app = FastAPI()
app.include_router(hr_tools.router)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends()):

    user = authenticate_user(form_data.username, form_data.password)

    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({
        "sub": user["username"],
        "role": user["role"]
    })

    return {
        "access_token": token,
        "token_type": "bearer"
    }



@app.get("/protected")
def protected(current_user=Depends(get_current_user)):

    return {
        "message": "Access granted",
        "user": current_user
    }
    

@app.get("/get_employee")
def get_employee(current_user=Depends(get_current_user)):
    return {
        "employee": "John Doe",
        "department": "Engineering",
        "requested_by": current_user
    }
    

def require_role(allowed_roles):

    def role_checker(user=Depends(get_current_user)):

        user_role = user["role"]

        if user_role not in allowed_roles:
            raise HTTPException(
                status_code=403,
                detail="Access forbidden for this role"
            )

        return user

    return role_checker

# testing code

# @app.get("/get_partner")
# def get_partner(user=Depends(require_role(
#     ["viewer","operator","sales_agent","manager","admin"]
# ))):

#     return {
#         "message": "Partner data returned",
#         "requested_by": user["sub"],
#         "role": user["role"]
#     }
    
# @app.post("/create_partner")
# def create_partner(user=Depends(require_role(
#     ["operator","sales_agent"]
# ))):

#     return {
#         "message": "Partner created",
#         "requested_by": user["sub"]
#     }
    
@app.post("/update_lead_stage")
def update_lead_stage(user=Depends(require_role(["manager"]))):

    return {
        "message": "Lead stage updated",
        "requested_by": user["sub"]
    }



