from sqlalchemy import Column, Integer, String, Float, DateTime, func, UniqueConstraint
from database import Base

class Country(Base):
    """
    Database model for the 'countries' table.
    """
    __tablename__ = "countries"

    id = Column(Integer, primary_key=True, index=True)
    
    name = Column(String(100), unique=True, index=True, nullable=False)
    
    capital = Column(String(100), nullable=True)
    region = Column(String(100), nullable=True)
    population = Column(Integer, nullable=False)
    currency_code = Column(String(10), nullable=True)
    exchange_rate = Column(Float, nullable=True)
    estimated_gdp = Column(Float, nullable=True)
    flag_url = Column(String(255), nullable=True)
    
    last_refreshed_at = Column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        onupdate=func.now()
    )

    __table_args__ = (UniqueConstraint('name', name='_name_uc'),)


class Status(Base):
    """
    Database model for the 'status' table.
    This will store global app status, like the last refresh time.
    """
    __tablename__ = "status"

    id = Column(Integer, primary_key=True, default=1)
    
    total_countries = Column(Integer, default=0)
    

    last_refreshed_at = Column(DateTime(timezone=True), nullable=True)