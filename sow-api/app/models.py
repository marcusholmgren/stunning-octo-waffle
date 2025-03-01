from pydantic import BaseModel, Field

class WaffleReview(BaseModel):
    restaurant: str = Field(..., title="Restaurant Name", max_length=100)
    review: str = Field(..., title="Review", max_length=500)
