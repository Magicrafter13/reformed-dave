# syntax=docker/dockerfile:1

FROM python:3.12

EXPOSE 8080

LABEL org.opencontainers.image.title="Reformed Dave"
LABEL org.opencontainers.image.description="Presbyterian theologian chatbot."
LABEL org.opencontainers.image.authors="self@matthewrease.net"
LABEL com.portainer.envvars=""

#RUN ["ln", "-s", "/usr/bin/python", "/usr/bin/python3"]

# Runtime

ENV PYTHONDONTWRITEBYTECODE=1

# Files

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt --root-user-action

COPY discord_bot.py ./
#ADD https://www.nerdfonts.com/assets/css/webfont.css blog/static/nerdfont.css
