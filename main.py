from typing import Optional
from fastapi import FastAPI, HTTPException, Depends, Security, Header  # type: ignore
from fastapi.security import APIKeyHeader # type: ignore
from sqlmodel import Field, SQLModel, create_engine, Session, select  # type: ignore
import os
import uvicorn  # type: ignore
from sqlalchemy.exc import IntegrityError

# Database model
class FoodProduct(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=100)
    ingredients: str = Field(max_length=10000)


# Set up database engine
db_url = os.environ.get("DATABASE_URL")
engine = create_engine(db_url)


app = FastAPI()


@app.get("/")
def read_root():
    return {"Hello": "World"}

# Dependency to get the database session
def get_session():
    with Session(engine) as session:
        yield session

# Get all food products
@app.get("/all-products")
def get_all_products(skip: int = 0, limit: int = 10, session: Session = Depends(get_session)):
    query = select(FoodProduct).offset(skip).limit(limit)
    products = session.exec(query).all()
    return products

# API key configuration
API_KEY = os.environ.get("API_KEY")
if not API_KEY:
    raise RuntimeError("API_KEY environment variable is not set")

api_key_header = APIKeyHeader(name="X-API-Key")

# Function to verify the API Key
async def verify_api_key(api_key: str = Security(api_key_header)):
    if api_key != API_KEY:
        raise HTTPException(
            status_code=403,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    return api_key


# Add a product to the database
@app.post("/add-product")
def add_product(item: FoodProduct, session: Session = Depends(get_session), api_key: str = Depends(verify_api_key)):
    
    statement = select(FoodProduct).where(FoodProduct.name == item.name)
    results = session.exec(statement)
    existing_product = results.first()  # Fetches the first matching result or None if no match found.

    if existing_product:
        raise HTTPException(status_code=409, detail="Product with the same name already exists.")
    
    session.add(item)
    try:
        session.commit()
        session.refresh(item)
        return item # Return the newly added item.
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail="An unexpected error occurred.")

# Get a specific ingredient
@app.get("/product/{product_name}")
def get_ingredient(product_name: str, session: Session = Depends(get_session)):
    statement = select(FoodProduct).where(FoodProduct.name.contains(product_name))
    results = session.exec(statement).first()
    
    if not results:
        raise HTTPException(status_code=404, detail="Ingredient not found")
    return results


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
