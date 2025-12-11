# Use Python 3.11 slim
FROM python:3.11-slim


# Set working directory
WORKDIR /app


# Copy repo into container
COPY . /app


# Install dependencies
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt


# Expose Streamlit port
EXPOSE 8501


# Run Streamlit (HF needs CORS disabled for Docker)
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.enableCORS=false"]