FROM mcr.microsoft.com/playwright/python:v1.44.0-jammy
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
RUN playwright install chromium
CMD ["python", "monitor.py"]