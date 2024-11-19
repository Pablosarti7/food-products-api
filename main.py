from typing import Optional
from fastapi import FastAPI  # type: ignore
from sqlmodel import Field, SQLModel, create_engine, Session, select  # type: ignore
import os
import uvicorn  # type: ignore

# Database model
class FoodProduct(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=100)
    ingredients: str = Field(max_length=500)


# Set up database engine
db_url = os.environ.get("DATABASE_URL")
engine = create_engine(db_url)


app = FastAPI()


@app.get("/")
def read_root():
    return {"Hello": "World"}

# Get all food products
@app.get("/all-products")
def get_all_products():
    with Session(engine) as session:
        heroes = session.exec(select(FoodProduct)).all()
        return heroes

# Add a product to the database
@app.post("/add-product")
def add_product(item: FoodProduct):
    with Session(engine) as session:
        session.add(item)
        session.commit()
        session.refresh(item)
    return item


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

