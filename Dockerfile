FROM ghcr.io/home-assistant/base:latest

RUN apk add --no-cache python3 py3-pip
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt /
RUN pip install --no-cache-dir -r /requirements.txt

COPY app.py /
COPY run.sh /
RUN chmod a+x /run.sh

CMD [ "/run.sh" ]
