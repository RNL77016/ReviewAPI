from fastapi import FastAPI, Depends, HTTPException, File, UploadFile, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
import shutil
import os

app = FastAPI()

# Configuración de la base de datos SQLite
DATABASE_URL = "sqlite:///./movies.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Montar la carpeta 'images' para servir archivos estáticos
app.mount("/images", StaticFiles(directory="images"), name="images")

# Modelos de base de datos
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)

class Movie(Base):
    __tablename__ = "movies"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, unique=True, index=True)
    description = Column(String)
    year = Column(Integer)
    genre = Column(String)
    rating = Column(Float)
    image_url = Column(String, nullable=True)

    reviews = relationship("Review", back_populates="movie")

class Review(Base):
    __tablename__ = "reviews"
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
    rating: float = Field(..., ge=1, le=10)

class ReviewCreate(BaseModel):
    content: str
    rating: float = Field(..., ge=1, le=10)

# Middleware para manejo global de excepciones
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    try:
        response = await call_next(request)
        return response
    except Exception as exc:
        return JSONResponse(
            status_code=500,
            content={"message": "An unexpected error occurred.", "details": str(exc)},
        )

# Endpoints de la API
@app.post("/user/")
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = User(email=user.email, password=user.password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return {
        "userId": db_user.id,
        "isLogged": True,
        "message": "Usuario creado correctamente"
    }

@app.post("/login/")
def login_user(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if not db_user or db_user.password != user.password:
        return {
            "userId": 0,
            "isLogged": False,
            "message": "Usuario o contraseña incorrectos"
        }
    return {
        "userId": db_user.id,
        "isLogged": True,
        "message": "Bienvenido"
    }

@app.get("/users/")
def get_users(db: Session = Depends(get_db)):
    return db.query(User).all()

@app.post("/movies/")
def create_movie(
    movie: MovieCreate,
    image: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    image_path = f"images/{image.filename}"
    with open(image_path, "wb") as buffer:
        shutil.copyfileobj(image.file, buffer)

    db_movie = Movie(
        title=movie.title,
        description=movie.description,
        year=movie.year,
        genre=movie.genre,
        rating=movie.rating,
        image_url=f"/images/{image.filename}"
    )
    db.add(db_movie)
    db.commit()
    db.refresh(db_movie)
    return db_movie

@app.get("/movies/")
def get_movies(db: Session = Depends(get_db)):
    return db.query(Movie).all()

@app.get("/movies({movie_id}")
def get_movie(movie_id: int, db: Session = Depends(get_db)):
    movie = db.query(Movie).filter(Movie.id == movie_id).first()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    return movie

@app.get("/movies/title/{title}")
def get_movie_by_title(title: str, db: Session = Depends(get_db)):
    movies = db.query(Movie).filter(Movie.title == title).all()
    if not movies:
        raise HTTPException(status_code=404, detail="Movie not found")
    return movies

@app.get("/movies/genre/{genre}")
def get_movie_by_genre(genre: str, db: Session = Depends(get_db)):
    movies = db.query(Movie).filter(Movie.genre == genre).all()
    if not movies:
        raise HTTPException(status_code=404, detail="Movie not found")
    return movies

@app.put("/movies/{movie_id}")
def update_movie(movie_id: int, movie: MovieCreate, db: Session = Depends(get_db)):
    db_movie = db.query(Movie).filter(Movie.id == movie_id).first()
    if not db_movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    db_movie.title = movie.title
    db_movie.description = movie.description
    db_movie.year = movie.year
    db_movie.genre = movie.genre
    db_movie.rating = movie.rating
    db_movie.image_url = movie.image_url
    db.commit()
    return db_movie

@app.delete("/movies/{movie_id}")
def delete_movie(movie_id: int, db: Session = Depends(get_db)):
    db_movie = db.query(Movie).filter(Movie.id == movie_id).first()
    if not db_movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    db.delete(db_movie)
    db.commit()
    return {"detail": "Movie deleted"}

@app.post("/movies/{title}/reviews/")
def create_review(title: str, review: ReviewCreate, db: Session = Depends(get_db)):
    db_movie = db.query(Movie).filter(Movie.title == title).first()
    if not db_movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    db_review = Review(content=review.content, rating=review.rating, movie_id=db_movie.id)
    db.add(db_review)
    db.commit()
    db.refresh(db_review)
    return db_review

app.get("/movies/{movie_id}/reviews/")
def get_reviews_by_movie_id(movie_id: int, db: Session = Depends(get_db)):
    db_movie = db.query(Movie).filter(Movie.id == movie_id).first()
    if not db_movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    reviews = db.query(Review).filter(Review.movie_id == db_movie.id).all()
    return reviews

@app.get("/movies/{title}/reviews/")
def get_reviews_by_title(title: str, db: Session = Depends(get_db)):
    db_movie = db.query(Movie).filter(Movie.title == title).first()
    if not db_movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    reviews = db.query(Review).filter(Review.movie_id == db_movie.id).all()
    return reviews

@app.get("/reviews/")
def get_all_reviews(db: Session = Depends(get_db)):
    return db.query(Review).all()

@app.put("/reviews/{review_id}")
def update_review(review_id: int, review: ReviewCreate, db: Session = Depends(get_db)):
    db_review = db.query(Review).filter(Review.id == review_id).first()
    if not db_review:
        raise HTTPException(status_code=404, detail="Review not found")
    db_review.content = review.content
    db_review.rating = review.rating
    db.commit()
    return db_review

@app.delete("/reviews/{review_id}")
def delete_review(review_id: int, db: Session = Depends(get_db)):
    db_review = db.query(Review).filter(Review.id == review_id).first()
    if not db_review:
        raise HTTPException(status_code=404, detail="Review not found")
    db.delete(db_review)
    db.commit()
    return {"detail": "Review deleted"}