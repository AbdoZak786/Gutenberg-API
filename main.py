"""
Project Gutenberg Books API
A REST API for querying and retrieving books from Project Gutenberg
"""

from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, or_, and_, func
from sqlalchemy.orm import sessionmaker, joinedload
from dotenv import load_dotenv  
from typing import List, Optional
from pydantic import BaseModel
import os

# Database models \
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, ForeignKey, Table
from sqlalchemy.orm import relationship

Base = declarative_base()
load_dotenv()
# Association tables
book_authors = Table('books_book_authors', Base.metadata,
    Column('book_id', Integer, ForeignKey('books_book.id')),
    Column('author_id', Integer, ForeignKey('books_author.id'))
)

book_subjects = Table('books_book_subjects', Base.metadata,
    Column('book_id', Integer, ForeignKey('books_book.id')),
    Column('subject_id', Integer, ForeignKey('books_subject.id'))
)

book_bookshelves = Table('books_book_bookshelves', Base.metadata,
    Column('book_id', Integer, ForeignKey('books_book.id')),
    Column('bookshelf_id', Integer, ForeignKey('books_bookshelf.id'))
)

book_languages = Table('books_book_languages', Base.metadata,
    Column('book_id', Integer, ForeignKey('books_book.id')),
    Column('language_id', Integer, ForeignKey('books_language.id'))
)

# Models
class Book(Base):
    __tablename__ = 'books_book'
    
    id = Column(Integer, primary_key=True)
    title = Column(String)
    download_count = Column(Integer, default=0)
    
    authors = relationship('Author', secondary=book_authors, back_populates='books')
    subjects = relationship('Subject', secondary=book_subjects, back_populates='books')
    bookshelves = relationship('Bookshelf', secondary=book_bookshelves, back_populates='books')
    languages = relationship('Language', secondary=book_languages, back_populates='books')
    formats = relationship('Format', back_populates='book')

class Author(Base):
    __tablename__ = 'books_author'
    
    id = Column(Integer, primary_key=True)
    name = Column(String)
    birth_year = Column(Integer, nullable=True)
    death_year = Column(Integer, nullable=True)
    
    books = relationship('Book', secondary=book_authors, back_populates='authors')

class Subject(Base):
    __tablename__ = 'books_subject'
    
    id = Column(Integer, primary_key=True)
    name = Column(String)
    
    books = relationship('Book', secondary=book_subjects, back_populates='subjects')

class Bookshelf(Base):
    __tablename__ = 'books_bookshelf'
    
    id = Column(Integer, primary_key=True)
    name = Column(String)
    
    books = relationship('Book', secondary=book_bookshelves, back_populates='bookshelves')

class Language(Base):
    __tablename__ = 'books_language'
    
    id = Column(Integer, primary_key=True)
    code = Column(String)
    
    books = relationship('Book', secondary=book_languages, back_populates='languages')

class Format(Base):
    __tablename__ = 'books_format'
    
    id = Column(Integer, primary_key=True)
    mime_type = Column(String)
    url = Column(String)
    book_id = Column(Integer, ForeignKey('books_book.id'))
    
    book = relationship('Book', back_populates='formats')

# Pydantic models for API responses
class AuthorInfo(BaseModel):
    name: str
    birth_year: Optional[int] = None
    death_year: Optional[int] = None
    
    class Config:
        from_attributes = True

class DownloadLink(BaseModel):
    mime_type: str
    url: str
    
    class Config:
        from_attributes = True

class BookResponse(BaseModel):
    id: int
    title: str
    authors: List[AuthorInfo]
    genres: List[str]  # subjects
    languages: List[str]
    subjects: List[str]
    bookshelves: List[str]
    download_links: List[DownloadLink]
    
    class Config:
        from_attributes = True

class BooksListResponse(BaseModel):
    count: int
    results: List[BookResponse]
    page: int
    total_pages: int

# Database connection
DATABASE_URL = os.getenv(
    'DATABASE_URL',
    'postgresql://user:password@localhost:5432/gutenberg'
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# FastAPI app
app = FastAPI(
    title="Project Gutenberg Books API",
    description="API for querying books from Project Gutenberg repository",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def parse_comma_separated(value: Optional[str]) -> List[str]:
    if not value:
        return []
    return [v.strip() for v in value.split(',') if v.strip()]

@app.get("/")
def root():
    return {
        "message": "Project Gutenberg Books API",
        "docs": "/docs",
        "endpoints": {
            "books": "/books - Query books with filters"
        }
    }

@app.get("/books", response_model=BooksListResponse)
def get_books(
    book_id: Optional[str] = Query(None, description="Comma-separated book IDs"),
    language: Optional[str] = Query(None, description="Comma-separated language codes (e.g., en,fr)"),
    mime_type: Optional[str] = Query(None, description="Comma-separated mime-types"),
    topic: Optional[str] = Query(None, description="Comma-separated topics (searches subjects and bookshelves)"),
    author: Optional[str] = Query(None, description="Comma-separated author names (partial match)"),
    title: Optional[str] = Query(None, description="Comma-separated title keywords (partial match)"),
    page: int = Query(1, ge=1, description="Page number (starts at 1)"),
    page_size: int = Query(25, ge=1, le=100, description="Number of results per page")
):
    """
    Query books with various filters.
    
    - Returns up to 25 books per page by default
    - Results sorted by download count (popularity) in descending order
    - Supports multiple filter criteria and multiple values per criterion
    - All text searches are case-insensitive
    """
    
    db = SessionLocal()
    try:
        # Start with base query
        query = db.query(Book).options(
            joinedload(Book.authors),
            joinedload(Book.subjects),
            joinedload(Book.bookshelves),
            joinedload(Book.languages),
            joinedload(Book.formats)
        )
        
        # Apply filters
        filters = []
        
        # Book ID filter
        if book_id:
            book_ids = [int(bid) for bid in parse_comma_separated(book_id)]
            filters.append(Book.id.in_(book_ids))
        
        # Language filter
        if language:
            languages = parse_comma_separated(language)
            query = query.join(Book.languages)
            filters.append(Language.code.in_(languages))
        
        # Mime-type filter
        if mime_type:
            mime_types = parse_comma_separated(mime_type)
            query = query.join(Book.formats)
            filters.append(Format.mime_type.in_(mime_types))
        
        # Topic filter (subjects OR bookshelves)
        if topic:
            topics = parse_comma_separated(topic)
            topic_conditions = []
            
            for t in topics:
                pattern = f"%{t}%"
                # Search in subjects
                subject_match = db.query(Subject.id).filter(
                    func.lower(Subject.name).like(func.lower(pattern))
                ).subquery()
                
                # Search in bookshelves
                bookshelf_match = db.query(Bookshelf.id).filter(
                    func.lower(Bookshelf.name).like(func.lower(pattern))
                ).subquery()
                
                topic_conditions.append(or_(
                    Book.subjects.any(Subject.id.in_(subject_match)),
                    Book.bookshelves.any(Bookshelf.id.in_(bookshelf_match))
                ))
            
            if topic_conditions:
                filters.append(or_(*topic_conditions))
        
        # Author filter
        if author:
            authors = parse_comma_separated(author)
            author_conditions = []
            
            for a in authors:
                pattern = f"%{a}%"
                author_conditions.append(
                    Book.authors.any(func.lower(Author.name).like(func.lower(pattern)))
                )
            
            if author_conditions:
                filters.append(or_(*author_conditions))
        
        # Title filter
        if title:
            titles = parse_comma_separated(title)
            title_conditions = []
            
            for t in titles:
                pattern = f"%{t}%"
                title_conditions.append(func.lower(Book.title).like(func.lower(pattern)))
            
            if title_conditions:
                filters.append(or_(*title_conditions))
        
        # Apply all filters
        if filters:
            query = query.filter(and_(*filters))
        
        # Remove duplicates (from joins)
        query = query.distinct()
        
        # Get total count
        total_count = query.count()
        
        # Sort by popularity (download_count)
        query = query.order_by(Book.download_count.desc())
        
        # Apply pagination
        offset = (page - 1) * page_size
        books = query.offset(offset).limit(page_size).all()
        
        # Format response
        results = []
        for book in books:
            results.append(BookResponse(
                id=book.id,
                title=book.title or "Unknown",
                authors=[
                    AuthorInfo(
                        name=author.name,
                        birth_year=author.birth_year,
                        death_year=author.death_year
                    )
                    for author in book.authors
                ],
                genres=[subject.name for subject in book.subjects],
                languages=[lang.code for lang in book.languages],
                subjects=[subject.name for subject in book.subjects],
                bookshelves=[shelf.name for shelf in book.bookshelves],
                download_links=[
                    DownloadLink(mime_type=fmt.mime_type, url=fmt.url)
                    for fmt in book.formats
                ]
            ))
        
        total_pages = (total_count + page_size - 1) // page_size
        
        return BooksListResponse(
            count=total_count,
            results=results,
            page=page,
            total_pages=total_pages
        )
        
    finally:
        db.close()

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)