from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
from pydantic import BaseModel
from sqlalchemy.orm import Session
import shutil
import os


app = FastAPI()

# Configuración de la base de datos SQLite
DATABASE_URL = "sqlite:///./movies.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Modelos de base de datos
class User(Base):
    _tablename_ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)

class Movie(Base):
    _tablename_ = "movies"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, unique=True, index=True)
    description = Column(String)
    year = Column(Integer)
    genre = Column(String)
    rating = Column(Float)
    image_url = Column(String, nullable=True)

    reviews = relationship("Review", back_populates="movie")

class Review(Base):
    _tablename_ = "reviews"
    id = Column(Integer, primary_key=True, index=True)
    content = Column(String)
    rating = Column(Float)
    movie_id = Column(Integer, ForeignKey("movies.id"))
    movie = relationship("Movie", back_populates="reviews")

# Crear las tablas en la base de datos
Base.metadata.create_all(bind=engine)

# Dependencia para obtener la sesión de la base de datos
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Modelos Pydantic
class UserCreate(BaseModel):
    email: str
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

class MovieCreate(BaseModel):
    title: str
    description: str
    year: int
    genre: str
    rating: float

class ReviewCreate(BaseModel):
    content: str
    rating: float

# Endpoints de la API
@app.post("/user/")
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = User(email=user.email, password=user.password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.post("/login/")
def login_user(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if not db_user or db_user.password != user.password:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return {"message": "Login successful"}

@app.get("/users/")
def get_users(db: Session = Depends(get_db)):
    return db.query(User).all()

