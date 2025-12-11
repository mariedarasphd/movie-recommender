# Use lightweight Python
FROM python:3.11-slim


# Set working directory
WORKDIR /app


# Copy all repo files into container
COPY . /app


# Install dependencies from requirements.txt
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt


# Expose Streamlit port
EXPOSE 8501


# Run Streamlit app with CORS disabled for HF Spaces
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.enableCORS=false"]