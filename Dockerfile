FROM python:3.10

WORKDIR /app

# Install git and clone the repo
RUN apt-get update && apt-get install -y git \
    && git clone https://github.com/FundsRFun/funds-ekosistem.git . \
    && pip install --no-cache-dir -r requirements.txt

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

EXPOSE 8000

CMD ["gunicorn", "funding.wsgi:application", "--bind", "0.0.0.0:8000"]