FROM python:3.13-rc-bookworm⁠
WORKDIR /
EXPOSE 3000
COPY . .
CMD [ "python3", "eribot.py" ]
