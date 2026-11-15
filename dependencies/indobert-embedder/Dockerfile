FROM python:3.11-slim

WORKDIR /app

# Pasang PyTorch CPU-only dan dependensi FastAPI
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu \
    && pip install --no-cache-dir transformers fastapi "uvicorn[standard]" pydantic

COPY app.py /app/app.py

EXPOSE 8001

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8001"]

