from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.responses import FileResponse, JSONResponse
from typing import List, Optional
import schemas
import os

from sqlalchemy.orm import Session

import crud
from crud import ExternalApiError
import models
from database import engine, get_db

models.Base.metadata.create_all(bind=engine)

app = FastAPI()
IMAGE_PATH = os.path.join("cache", "summary.png")


@app.get("/")
def read_root():
    """
    Root endpoint to check if the API is running.
    """
    return {"message": "Hello, welcome to the Country API!"}


@app.post("/countries/refresh", status_code=status.HTTP_200_OK)
async def refresh_countries_data(db: Session = Depends(get_db)):
    try:
        result = await crud.refresh_all_countries(db)
        return result
        
    except ExternalApiError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": "External data source unavailable",
                "details": f"Could not fetch data from {e.service_name}: {e.message}"
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Internal server error", "details": str(e)}
        )


@app.get("/countries/image")
async def get_summary_image():
    """
    Serves the generated summary image.
    Returns a 404 if the image has not been generated yet.
    """
    if not os.path.exists(IMAGE_PATH):
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"error": "Summary image not found"}
        )
    return FileResponse(IMAGE_PATH, media_type="image/png")

@app.get("/status", response_model=schemas.StatusResponse)
async def get_status(db: Session = Depends(get_db)):
    """
    Shows total countries in the DB and the last refresh timestamp.
    """
    status = crud.get_app_status(db)
    if not status:
        return schemas.StatusResponse(total_countries=0, last_refreshed_at=None)
    
    return status


@app.get("/countries/{name}", response_model=schemas.CountryResponse)
async def get_country(name: str, db: Session = Depends(get_db)):
    """
    Gets a single country's details by its name (case-insensitive).
    """
    country = crud.get_country_by_name(db, name)
    
    if not country:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "Country not found"}
        )
        
    return country


@app.delete("/countries/{name}", status_code=status.HTTP_200_OK)
async def delete_country(name: str, db: Session = Depends(get_db)):
    """
    Deletes a country's record by its name (case-insensitive).
    """
    deleted_country = crud.delete_country_by_name(db, name)
    
    if not deleted_country:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "Country not found"}
        )
        
    #return a simple confirmation if successful
    return {
        "message": "Country deleted successfully",
        "deleted_country": deleted_country.name
    }

@app.get("/countries", response_model=List[schemas.CountryResponse])
async def get_all_countries(
    region: Optional[str] = None,
    currency: Optional[str] = None,
    sort: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Gets a list of all countries.
    Supports filtering by 'region' (case-insensitive contains)
    and 'currency' (case-insensitive exact match).
    Supports sorting by: 'name_asc', 'name_desc', 'population_asc', 
    'population_desc', 'gdp_asc', 'gdp_desc'.
    """
    countries = crud.get_countries(
        db, region=region, currency=currency, sort=sort
    )
    return countries