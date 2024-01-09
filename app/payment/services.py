from app.settings.database import database
from pydantic import BaseModel
from pydantic import  ValidationError
from typing import Optional

from fastapi import HTTPException
import stripe
import os
from dotenv import load_dotenv

env_path = os.path.join(".", ".env")
load_dotenv(dotenv_path=env_path)
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

class PaymentBase(BaseModel):
    amount: int
    accepted: Optional[bool] = False

class CreatePayment(PaymentBase):
    user_id: int
    product_id: int

class UpdatePayment(BaseModel):
    product_id: int
    amount: int

class Payment(PaymentBase):
    id: int
    user_id: int
    payment_id: int
    amount: int

class AbstractModel(PaymentBase):
    payment_method: str
    
class ConfirmPayment(AbstractModel):
    product_id: int
    

class PaymentService:
    def __init__(self):
        self.repository = database

    async def find_payment(self, payment_id: int):
        payment = await self.repository.payment.find_first(where={"id": payment_id})
        if not payment:
                raise HTTPException(status_code=404, detail="Payment ID not found")

        user = await self.repository.user.find_first(where={"id":payment.user_id})
        product = await self.repository.product.find_first(where={"id":payment.product_id})
        payment_info_by_id = {
                    "payment_id": payment.id,
                    "user_id": user.id if user else None,
                    "user_name": user.name if user else None,
                    "product_id": product.id if product else None,
                    "product_name": product.name if product else None,
                    "product_description": product.description if product else None, 
                    "amount": payment.amount,
                    "accepted": payment.accepted,
                    "created_at": payment.created_at.isoformat(),
                    "updated_at": payment.updated_at.isoformat(),
        }
            
        return payment_info_by_id
    
    
    async def find_all_payment(self):
        
        payments = await self.repository.payment.find_many()

        payment_history = []
        for payment in payments:
        
            user = await self.repository.user.find_first(where={"id": payment.user_id})
            product = await self.repository.product.find_first(where={"id": payment.product_id})

            payment_info = {
                "payment_id": payment.id,
                "user_id": user.id if user else None,
                "user_name": user.name if user else None,
                "product_id": product.id if product else None,
                "product_name": product.name if product else None,
                "product_description": product.description if product else None, 
                "amount": payment.amount,
                "accepted": payment.accepted,
                "created_at": payment.created_at.isoformat(),
                "updated_at": payment.updated_at.isoformat(),
            }
            payment_history.append(payment_info)

        return payment_history

    #This method will create a payment intent
    async def create_payment(self, payment: CreatePayment):
    
            user_exists = await self.repository.user.find_first(where={"id": payment.user_id})
            if not user_exists:
                return {"error": "User not found"}

            product_exists = await self.repository.product.find_first(where={"id": payment.product_id})
            if not product_exists:
                return {"error": "Product not found"}
            
            new_payment = await self.repository.payment.create(data = payment.dict())

            payment_info = {
                "payment id": new_payment.id,
                "user id": user_exists.id,
                "user name": user_exists.name,
                "product id": product_exists.id,
                "product": product_exists.name,
                "product description": product_exists.description, 
                "amount": new_payment.amount,
                "created_at": new_payment.created_at.isoformat(),
                "updated_at": new_payment.updated_at.isoformat(),
                }
            # print(f'payment info: {payment_info}') 
            payment_id = payment_info["payment id"]
            # print(f'payment id: {payment_id}')
            amount = payment_info["amount"]
            # print(f'amount: {amount}')
            confirm_payment_url = 'localhost:8000/confirm'
            try:
                payment_intent = await self.stripe_payment_intent(new_payment.id)
                
                if payment_intent.get("Success"):
                    new_payment.accepted = True
                    await self.repository.payment.update(data = {"accepted": True}, where={"id": new_payment.id})
                    
                    charge = payment_intent["charge"]
                    payment_intent_id = payment_intent["payment_intent_id"]
                    payment_method = payment_intent["payment_method"]
                    payment_status = payment_intent["status"]
                    return {"message": "Payment created successfully", "payment_info": payment_info, "charge": charge,"payment_intent_id":payment_intent_id, "payment_method": payment_method, "payment_status": payment_status, "redirect url": confirm_payment_url}, 201
                
                else:
                    return {"error": "Payment processing failed", "details": payment_intent.get("error")}, 400
            
            except HTTPException as http_exc:
                print(f"Se ha producido una excepción HTTP: {http_exc.detail}")
                raise HTTPException(status_code=http_exc.status_code, detail=http_exc.detail)
            
            except Exception as ex:
                return {"error": str(ex)}, 500

   #Confirm Payment method
        
    async def stripe_payment_confirm(self, payment_intent_id: str, payment_method: str):
        try:     
  
             result = stripe.PaymentIntent.confirm(payment_intent_id, payment_method=payment_method, return_url="https://www.example.com",
), 
             return result
        except Exception as ex:
             return {"message": f"An error has ocurred {ex}"}



    async def update_payment(self, payment_id: int, payment: UpdatePayment):

                payment_exists = await self.repository.payment.find_first(where={"id": payment_id})
                
                if not payment_exists:
                    raise HTTPException(status_code=404, detail="Payment ID not found")

                updated_payment = await self.repository.payment.update(
                    where={"id": payment_id},
                    data=payment.dict(),
                
                )
                
                product = await self.repository.product.find_first(where={"id": payment.product_id})
                if not product:
                    return {"error": "Product not found"}
                
                product = await self.repository.product.find_first(where={"id": updated_payment.product_id})
                if product:
                    payment_info = {
                        "id": updated_payment.id,
                        "amount": updated_payment.amount,
                        "accepted": updated_payment.accepted,
                        "created_at": updated_payment.created_at.isoformat(),
                        "updated_at": updated_payment.updated_at.isoformat(),
                    }
                    payment_info["product"] = product.name
    
                return {
                    "message": f'Payment {payment_id} updated successfully',
                    "payment": payment_info
                }
                    
        
    async def delete_payment(self, payment_id: int):
        payment_exists = await self.repository.payment.find_first(where={"id": payment_id})
        if not payment_exists:
            raise HTTPException(status_code=404, detail="Payment ID not found")        

        await self.repository.payment.delete(where={"id": payment_id})
        return  {"message": f"Payment {payment_id} deleted successfully"}, 200


#--------------------------------------------------
#          PAYMENT PROCESSING METHODS             #                        
#           (Stripe API v1 integration)           #
#--------------------------------------------------
            


    #This method will process the payment intent by charge the debit or credit card of the user
    async def stripe_payment_intent(self, payment_id: int):
        payment = await self.find_payment(payment_id)
        # print(f"¨¨¨payment associated:¨¨¨ {payment}")
        amount = payment["amount"]    
        # product_id = payment["produc7t id"]
        if not payment:
            return {"error": "Payment intent not found"}
        
        try:
            charge = "ch_1NirD82eZvKYlo2CIvbtLWuY" #foo value

            result = stripe.PaymentIntent.create(
            amount=amount,
            currency="usd",
            automatic_payment_methods={"enabled": True}, #obtained from Stripe dashboard
            description=charge        
            )
            return {"Success": True, "charge": charge, "payment_intent_id": result.id, "payment_method": result.payment_method, "status":result.status }
        except stripe.error.StripeError as e:
            
            return {"error": str(e)}