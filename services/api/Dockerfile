FROM python:3.12-slim-bookworm

WORKDIR /code

COPY ./requirements-linux.txt /code/requirements-linux.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements-linux.txt

# psycopg2 needed for entrypoint DB health check
RUN pip install --no-cache-dir psycopg2-binary

COPY . /code

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["/entrypoint.sh"]