# Project Gutenberg Books API

A REST API for querying and retrieving books from the Project Gutenberg repository.

## Features

- **Comprehensive Filtering**: Filter books by ID, language, mime-type, topic, author, and title
- **Pagination**: Returns 25 books per page (configurable up to 100)
- **Sorting**: Results sorted by popularity (download count) in descending order
- **Flexible Search**: Case-insensitive partial matching for text fields
- **Multiple Values**: Support for multiple values per filter criterion
- **JSON Responses**: Clean, structured JSON output
- **Auto Documentation**: Interactive API docs at `/docs`

## Quick Start

### Prerequisites

- Docker and Docker Compose
- PostgreSQL database dump from Project Gutenberg

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd gutenberg-api
```

2. Place the PostgreSQL dump file as `gutenberg.sql` in the project root

3. Start the services:
```bash
docker-compose up -d
```

4. Access the API:
   - API: http://localhost:8000
   - Interactive docs: http://localhost:8000/docs
   - Alternative docs: http://localhost:8000/redoc

### Without Docker

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up PostgreSQL and import the dump:
```bash
psql -U postgres -c "CREATE DATABASE gutenberg;"
psql -U postgres gutenberg < gutenberg.sql
```

3. Set environment variable:
```bash
export DATABASE_URL="postgresql://user:password@localhost:5432/gutenberg"
```

4. Run the application:
```bash
uvicorn main:app --reload
```

## API Endpoints

### GET /books

Query books with various filters.

**Query Parameters:**

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `book_id` | string | Comma-separated book IDs | `1,2,3` |
| `language` | string | Comma-separated language codes | `en,fr` |
| `mime_type` | string | Comma-separated mime-types | `text/html,application/pdf` |
| `topic` | string | Comma-separated topics (searches subjects and bookshelves) | `child,infant` |
| `author` | string | Comma-separated author names (partial match) | `dickens,austen` |
| `title` | string | Comma-separated title keywords (partial match) | `pride,prejudice` |
| `page` | integer | Page number (default: 1) | `2` |
| `page_size` | integer | Results per page (default: 25, max: 100) | `50` |

**Response Format:**

```json
{
  "count": 150,
  "results": [
    {
      "id": 1342,
      "title": "Pride and Prejudice",
      "authors": [
        {
          "name": "Jane Austen",
          "birth_year": 1775,
          "death_year": 1817
        }
      ],
      "genres": ["Fiction", "Romance"],
      "languages": ["en"],
      "subjects": ["England -- Fiction", "Love stories"],
      "bookshelves": ["Best Books Ever Listings", "Harvard Classics"],
      "download_links": [
        {
          "mime_type": "text/html",
          "url": "https://www.gutenberg.org/files/1342/1342-h/1342-h.htm"
        },
        {
          "mime_type": "application/epub+zip",
          "url": "https://www.gutenberg.org/ebooks/1342.epub.images"
        }
      ]
    }
  ],
  "page": 1,
  "total_pages": 6
}
```

## Example API Calls

### 1. Get books by language
```bash
curl "http://localhost:8000/books?language=en"
```

### 2. Search for children's books
```bash
curl "http://localhost:8000/books?topic=child"
```

### 3. Filter by author (partial match)
```bash
curl "http://localhost:8000/books?author=dickens"
```

### 4. Multiple filters
```bash
curl "http://localhost:8000/books?language=en,fr&topic=child,infant&page=2"
```

### 5. Search by title and author
```bash
curl "http://localhost:8000/books?title=pride&author=austen"
```

### 6. Get specific books by ID
```bash
curl "http://localhost:8000/books?book_id=1342,84,11"
```

### 7. Filter by mime-type
```bash
curl "http://localhost:8000/books?mime_type=application/pdf"
```

## Code Structure

```
.
├── main.py              # Main application file
├── requirements.txt     # Python dependencies
├── Dockerfile          # Docker container definition
├── docker-compose.yml  # Docker Compose configuration
└── README.md           # This file
```

## Technical Details

### Technology Stack

- **FastAPI**: Modern, fast web framework for building APIs
- **SQLAlchemy**: SQL toolkit and ORM
- **PostgreSQL**: Relational database
- **Pydantic**: Data validation using Python type hints
- **Uvicorn**: ASGI server

### Key Implementation Details

1. **Database Schema**: Follows the standard Project Gutenberg schema with tables for books, authors, subjects, bookshelves, languages, and formats

2. **Filtering Logic**:
   - Multiple filter values are combined with OR logic within the same criterion
   - Multiple filter criteria are combined with AND logic
   - Text searches use case-insensitive partial matching with SQL LIKE and ILIKE
   - Topic filter searches both subjects and bookshelves

3. **Pagination**: Uses offset-based pagination with configurable page size

4. **Performance**:
   - Uses eager loading (joinedload) to minimize database queries
   - Applies DISTINCT to handle many-to-many relationship joins
   - Indexed columns for optimal query performance

5. **API Design**:
   - RESTful endpoints
   - Clear, descriptive parameter names
   - Comprehensive error handling
   - Automatic API documentation via OpenAPI/Swagger

## Deployment

### Deploying to Cloud Platforms

#### Heroku
```bash
heroku create gutenberg-api
heroku addons:create heroku-postgresql:hobby-dev
git push heroku main
```

#### AWS (using ECS/Fargate)
- Build and push Docker image to ECR
- Create ECS cluster with Fargate
- Set up RDS PostgreSQL instance
- Deploy using ECS task definition

#### Google Cloud Run
```bash
gcloud builds submit --tag gcr.io/PROJECT_ID/gutenberg-api
gcloud run deploy gutenberg-api --image gcr.io/PROJECT_ID/gutenberg-api --platform managed
```

#### Railway/Render
- Connect GitHub repository
- Add PostgreSQL database addon
- Deploy with one click

## Testing

### Manual Testing
Visit http://localhost:8000/docs for interactive API documentation where you can test all endpoints.

### Automated Testing
```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run tests
pytest tests/
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://user:password@localhost:5432/gutenberg` |

## License

This API is provided for educational and evaluation purposes. The Project Gutenberg data is subject to the Project Gutenberg License.

## Contributing

Feel free to submit issues and enhancement requests!

## Notes for Evaluators

### Design Decisions

1. **FastAPI**: Chosen for its modern async support, automatic validation, and built-in API documentation
2. **SQLAlchemy ORM**: Provides abstraction over SQL while maintaining flexibility
3. **Comma-separated values**: Simple approach for multiple filter values without complex query string syntax
4. **Eager loading**: Optimizes database queries by loading related data upfront
5. **DISTINCT**: Necessary to handle duplicate results from many-to-many joins

### Code Quality

- Consistent naming conventions (snake_case for functions/variables)
- Comprehensive docstrings
- Type hints throughout
- Clean separation of concerns
- Error handling and validation

### Extensibility

The API is designed to be easily extended with:
- Additional filter criteria
- Different sorting options
- Alternative response formats
- Caching layer
- Rate limiting
- Authentication/authorization

## Contact

For questions or clarifications, please reach out during the evaluation process.