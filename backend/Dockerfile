# backend/Dockerfile
FROM python:3.10-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    libgl1-mesa-glx \
    libglib2.0-0 \
#    git \  
    curl && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install apscheduler python-dateutil
RUN pip install -r requirements.txt
RUN pip install requests
#RUN pip install git+https://github.com/VikParuchuri/surya.git
COPY ./src /app/src
EXPOSE 8000
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
