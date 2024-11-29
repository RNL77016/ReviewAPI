from fastapi import FastAPI
from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import sessionmaker, declarative_base, relationship

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

