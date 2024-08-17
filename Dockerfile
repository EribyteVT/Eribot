FROM python:3.9.13-slim-buster
WORKDIR /
EXPOSE 3000
COPY . .
CMD [ "python3", "eribot.py" ]
