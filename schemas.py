from pydantic import BaseModel
from datetime import datetime
from typing import Optional

# This is our main 'Country' response model.
# It defines the fields that will be returned to the user.
class CountryResponse(BaseModel):
    id: int
    name: str
    capital: Optional[str] = None
    region: Optional[str] = None
    population: int
    currency_code: Optional[str] = None
    exchange_rate: Optional[float] = None
    estimated_gdp: Optional[float] = None
    flag_url: Optional[str] = None
    last_refreshed_at: datetime

    # This 'Config' class tells Pydantic to work with
    # our SQLAlchemy models. It allows it to read data
    # directly from the database objects.
    class Config:
        orm_mode = True

# This is the model for our /status endpoint response
class StatusResponse(BaseModel):
    total_countries: int
    last_refreshed_at: Optional[datetime] = None