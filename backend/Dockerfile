# Use the official lightweight Python 3.12 image
FROM python:3.12-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the backend files
COPY . .

# Expose port 8000 for the FastAPI server
EXPOSE 8000

# When the container starts:
# 1. Run all our scrapers/seeders to initialize the SQLite database
# 2. Run the sentiment analyzer
# 3. Train and save the AI model
# 4. Start the FastAPI server using Uvicorn
CMD ["sh", "-c", "python scraper_mufap.py && python scraper_news.py && python scraper_market.py && python sentiment.py && python model.py && uvicorn main:app --host 0.0.0.0 --port 8000"]
