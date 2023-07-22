FROM python:3.10-bullseye

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt

RUN pip install --no-cache-dir --upgrade -r requirements.txt

COPY ./l1nkzip /code/l1nkzip

CMD ["uvicorn", "l1nkzip.main:app", "--proxy-headers", "--host", "0.0.0.0", "--port", "80"]
