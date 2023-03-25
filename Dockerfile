FROM alpine
ENV PYTHONUNBUFFERED=1
RUN apk add --update --no-cache python3 && ln -sf python3 /usr/bin/python
RUN python3 -m ensurepip
RUN pip3 install --no-cache --upgrade pip setuptools discord.py tinydb python-dotenv
RUN mkdir -p /usr/src/bot
WORKDIR /usr/src/bot
COPY . .
CMD [ "python", "bot.py" ]
