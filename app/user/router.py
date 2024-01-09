from fastapi import APIRouter, HTTPException, Depends

from app.user.services import CreateUser, UpdateUser, UserService

user_service = UserService

router = APIRouter(
    prefix="/users",
    tags=["users"],
    dependencies=[Depends(user_service)]
)

@router.get("")
async def get_all_users(user_service: UserService = Depends()):
    return await user_service.find_all_user()

@router.get("/{id:int}")
async def get_user(id: int, user_service: UserService = Depends()):
    return await user_service.find_user(user_id=id)

@router.post("/")
async def create_user(user: CreateUser, user_service: UserService=Depends()):
    try:
        new_user = await user_service.create_user(user)
        return new_user
    
    except Exception as ex:
        raise HTTPException(status_code=500, detail=f"Fuck! Internal Server Error: {str(ex)}")

@router.put("/{id}")
async def update_user(id: int, user: UpdateUser, user_service:UserService = Depends()):
    return await user_service.update_user(user_id=id, user=user)


@router.delete("/{id}")
async def delete_user(id: int, user_service: UserService = Depends()):
    return await user_service.delete_user(user_id=id)