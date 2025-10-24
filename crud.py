import httpx
import random
from datetime import datetime
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import SQLAlchemyError
from typing import Optional, List
from sqlalchemy import desc, asc
import os 
from PIL import Image, ImageDraw, ImageFont
import models

# --- Configuration ---
COUNTRIES_API_URL = "https://restcountries.com/v2/all?fields=name,capital,region,population,flag,currencies"
RATES_API_URL = "https://open.er-api.com/v6/latest/USD"

# --- 3. DEFINE IMAGE PATH ---
CACHE_DIR = "cache"
IMAGE_PATH = os.path.join(CACHE_DIR, "summary.png")

# ... (ExternalApiError class and fetch functions remain the same) ...
class ExternalApiError(Exception):
    def __init__(self, service_name: str, status_code: Optional[int] = None, message: Optional[str] = None):
        self.service_name = service_name
        self.status_code = status_code
        self.message = message or f"Error fetching data from {service_name}"
        super().__init__(self.message)

async def fetch_countries_data(client: httpx.AsyncClient) -> list:
    # ... (no change) ...
    try:
        response = await client.get(COUNTRIES_API_URL, timeout=10.0)
        response.raise_for_status()  # Raise an exception for 4xx or 5xx errors
        return response.json()
    except httpx.HTTPStatusError as e:
        raise ExternalApiError("restcountries.com", e.response.status_code, str(e))
    except httpx.RequestError as e:
        raise ExternalApiError("restcountries.com", message=str(e))

async def fetch_exchange_rates(client: httpx.AsyncClient) -> dict:
    # ... (no change) ...
    try:
        response = await client.get(RATES_API_URL, timeout=10.0)
        response.raise_for_status()
        return response.json().get("rates", {})
    except httpx.HTTPStatusError as e:
        raise ExternalApiError("open.er-api.com", e.response.status_code, str(e))
    except httpx.RequestError as e:
        raise ExternalApiError("open.er-api.com", message=str(e))


# --- 4. NEW IMAGE GENERATION FUNCTION ---
def generate_summary_image(db: Session, last_refresh_time: datetime):
    """
    Generates and saves a summary image with stats from the database.
    """
    try:
        # --- A. Query for Data ---
        total_countries = db.query(models.Country).count()
        
        # Query for Top 5 countries by estimated_gdp (descending)
        top_5_countries = db.query(models.Country).order_by(
            models.Country.estimated_gdp.is_(None),  # 1. Puts all NULLs last
            desc(models.Country.estimated_gdp)       # 2. Sorts non-NULLs highest-to-lowest
        ).limit(5).all()

        # --- B. Create the Image ---
        img_width = 500
        img_height = 300
        # Create a new white image
        img = Image.new('RGB', (img_width, img_height), color='white')
        d = ImageDraw.Draw(img)

        # --- C. Load a Font ---
        try:
            font_title = ImageFont.truetype("arial.ttf", 20)
            font_body = ImageFont.truetype("arial.ttf", 15)
        except IOError:
            font_title = ImageFont.load_default()
            font_body = ImageFont.load_default()

        # --- D. Draw the Text ---
        padding = 20
        d.text((padding, padding), "Country API Refresh Summary", fill='black', font=font_title)
        
        # Timestamp
        time_str = last_refresh_time.strftime('%Y-%m-%d %H:%M:%S UTC')
        d.text((padding, padding + 30), f"Last Refresh: {time_str}", fill='gray', font=font_body)

        # Total Countries
        d.text((padding, padding + 70), f"Total Countries Cached: {total_countries}", fill='black', font=font_body)

        # Top 5 List
        d.text((padding, padding + 110), "Top 5 Countries by Est. GDP:", fill='black', font=font_body)
        
        current_y = padding + 135
        for i, country in enumerate(top_5_countries):
            gdp_str = f"${country.estimated_gdp:,.2f}" if country.estimated_gdp is not None else "N/A"
            line = f"{i+1}. {country.name} ({gdp_str})"
            d.text((padding + 10, current_y), line, fill='black', font=font_body)
            current_y += 20 # Move down for the next line

        # --- E. Save the Image ---
        # Ensure the cache directory exists
        os.makedirs(CACHE_DIR, exist_ok=True)
        img.save(IMAGE_PATH)
        print(f"Summary image saved to {IMAGE_PATH}")

    except Exception as e:
        # We'll just print the error. Failing to create an image
        # shouldn't cause the whole /refresh endpoint to fail.
        print(f"Error generating summary image: {e}")


# --- Main Refresh Function (MODIFIED) ---
async def refresh_all_countries(db: Session) -> dict:
    """
    The main logic for the POST /countries/refresh endpoint.
    Fetches, processes, and "upserts" country data.
    """
    try:
        # ... (all the fetching and processing logic remains exactly the same) ...
        async with httpx.AsyncClient() as client:
            countries_data = await fetch_countries_data(client)
            rates_data = await fetch_exchange_rates(client)
        
        country_count = 0
        
        for country_data in countries_data:
            # ... (no change in this loop) ...
            country_name = country_data.get("name")
            
            if not country_name or country_data.get("population") is None:
                continue 
            
            currency_code = None
            exchange_rate = None
            currencies = country_data.get("currencies")
            
            if currencies and isinstance(currencies, list) and len(currencies) > 0:
                currency_code = currencies[0].get("code")
                if currency_code:
                    exchange_rate = rates_data.get(currency_code)

            estimated_gdp = None
            population = country_data.get("population", 0)

            if population > 0 and exchange_rate:
                random_multiplier = random.uniform(1000, 2000)
                estimated_gdp = (population * random_multiplier) / exchange_rate
            elif population > 0 and currency_code is not None and exchange_rate is None:
                estimated_gdp = None
            else:
                estimated_gdp = 0

            existing_country = db.query(models.Country).filter(
                models.Country.name.ilike(country_name)
            ).first()

            if existing_country:
                existing_country.capital = country_data.get("capital")
                existing_country.region = country_data.get("region")
                existing_country.population = population
                existing_country.flag_url = country_data.get("flag")
                existing_country.currency_code = currency_code  # type: ignore
                existing_country.exchange_rate = exchange_rate  # type: ignore
                existing_country.estimated_gdp = estimated_gdp  # type: ignore
            
            else:
                new_country = models.Country(
                    name=country_name,
                    capital=country_data.get("capital"),
                    region=country_data.get("region"),
                    population=population,
                    flag_url=country_data.get("flag"),
                    currency_code=currency_code,
                    exchange_rate=exchange_rate,
                    estimated_gdp=estimated_gdp
                )
                db.add(new_country)
            
            country_count += 1

        # ... (Status update logic remains the same) ...
        status_record = db.query(models.Status).filter(models.Status.id == 1).first()
        refresh_time = datetime.utcnow()

        if status_record:
            status_record.total_countries = country_count    # type: ignore
            status_record.last_refreshed_at = refresh_time # type: ignore
        else:
            new_status = models.Status(
                id=1,
                total_countries=country_count,
                last_refreshed_at=refresh_time
            )
            db.add(new_status)

        # --- 5. COMMIT CHANGES (NO CHANGE) ---
        db.commit()

        # --- 6. CALL IMAGE FUNCTION (NEW) ---
        # After the data is successfully committed,
        # we generate the summary image.
        generate_summary_image(db, refresh_time)

        return {
            "status": "success", 
            "total_countries_processed": country_count,
            "last_refreshed_at": refresh_time
        }

    except ExternalApiError as e:
        # ... (no change) ...
        db.rollback()
        raise e
    
    except SQLAlchemyError as e:
        # ... (no change) ...
        db.rollback()
        raise ExternalApiError("Database", message=str(e))
    
    except Exception as e:
        # ... (no change) ...
        db.rollback()
        raise e
    

def get_app_status(db: Session) -> Optional[models.Status]:
    """
    Fetches the global status (total count and last refresh) from the DB.
    """
    # We just grab the one row we know (id=1)
    return db.query(models.Status).filter(models.Status.id == 1).first()


# --- 2. NEW FUNCTION FOR /countries/:name ---
def get_country_by_name(db: Session, name: str) -> Optional[models.Country]:
    """
    Fetches a single country from the DB by its name (case-insensitive).
    """
    return db.query(models.Country).filter(models.Country.name.ilike(name)).first()


# --- 3. NEW FUNCTION FOR DELETE /countries/:name ---
def delete_country_by_name(db: Session, name: str) -> Optional[models.Country]:
    """
    Deletes a single country from the DB by its name (case-insensitive).
    Returns the deleted country object, or None if not found.
    """
    # First, find the country
    country_to_delete = db.query(models.Country).filter(models.Country.name.ilike(name)).first()
    
    if country_to_delete:
        # If we found it, delete it from the session
        db.delete(country_to_delete)
        # Commit the deletion
        db.commit()
    
    return country_to_delete

def get_countries(
    db: Session, 
    region: Optional[str] = None, 
    currency: Optional[str] = None, 
    sort: Optional[str] = None
) -> List[models.Country]:
    """
    Fetches all countries from the DB, with optional filters and sorting.
    """
    
    # Start with a base query to get all countries
    query = db.query(models.Country)
    
    # --- A. Apply Filters ---
    
    # If a region is provided, add a case-insensitive filter
    if region:
        query = query.filter(models.Country.region.ilike(f"%{region}%"))
        
    # If a currency is provided, add a case-insensitive filter
    if currency:
        query = query.filter(models.Country.currency_code.ilike(currency))
        
    # --- B. Apply Sorting ---
    
    # We define the allowed sort fields to prevent errors
    allowed_sort_fields = {
        "name_asc": asc(models.Country.name),
        "name_desc": desc(models.Country.name),
        "population_asc": asc(models.Country.population),
        "population_desc": desc(models.Country.population),
        "gdp_asc": asc(models.Country.estimated_gdp),
        "gdp_desc": desc(models.Country.estimated_gdp)
    }
    
    # Default sort
    sort_logic = asc(models.Country.name)

    if sort and sort in allowed_sort_fields:
        sort_logic = allowed_sort_fields[sort]
    
    # Apply the sorting
    query = query.order_by(sort_logic)
    
    # --- C. Execute Query ---
    # Finally, run the query and return all results
    return query.all()