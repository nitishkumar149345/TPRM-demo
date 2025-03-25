FROM python:3.12

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir -r requirements.txt

COPY .env.template .env

EXPOSE 5000

# CMD ["python","-m","uvicorn", "app.main:app", "--reload", "--port", "5000"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "5000", "--reload"]
