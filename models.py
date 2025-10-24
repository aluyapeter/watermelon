from sqlalchemy import Column, Integer, String, Float, DateTime, func, UniqueConstraint
from database import Base

class Country(Base):
    """
    Database model for the 'countries' table.
    """
    __tablename__ = "countries"

    # Define the columns for our table
    id = Column(Integer, primary_key=True, index=True)
    
    # We add a constraint to make sure country names are unique
    name = Column(String(100), unique=True, index=True, nullable=False)
    
    capital = Column(String(100), nullable=True)
    region = Column(String(100), nullable=True)
    population = Column(Integer, nullable=False)
    currency_code = Column(String(10), nullable=True)
    exchange_rate = Column(Float, nullable=True)
    estimated_gdp = Column(Float, nullable=True)
    flag_url = Column(String(255), nullable=True)
    
    # This column will automatically update its timestamp
    last_refreshed_at = Column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        onupdate=func.now()
    )

    # This ensures that a country name is unique, ignoring case (e.g., "Nigeria" and "nigeria")
    # Note: This might be more complex depending on the specific MySQL setup
    __table_args__ = (UniqueConstraint('name', name='_name_uc'),)


class Status(Base):
    """
    Database model for the 'status' table.
    This will store global app status, like the last refresh time.
    """
    __tablename__ = "status"

    # We use a simple ID, but we'll only ever have one row
    id = Column(Integer, primary_key=True, default=1)
    
    total_countries = Column(Integer, default=0)
    
    # This is the global timestamp for the last *successful* refresh
    last_refreshed_at = Column(DateTime(timezone=True), nullable=True)