FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY adx_api_upload.py .
ENTRYPOINT ["python", "adx_api_upload.py"]
