FROM python:3.10-slim

WORKDIR /app

# Set environment variables
ENV PYTHONPATH=/app \
    PYTHONUNBUFFERED=1
    # PYTHONDONTWRITEBYTECODE=1

# Install dependencies
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Create a non-root user for running the application
RUN addgroup --system --gid 1001 appgroup && \
    adduser --system --uid 1001 --gid 1001 appuser

COPY src/ /app/

# Set ownership of the application directory to the non-root user
RUN chown -R appuser:appgroup /app

USER appuser
EXPOSE 9000

CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "9000"]
