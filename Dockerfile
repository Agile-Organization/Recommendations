# Using a Linux micro-container
FROM python:3.7

# Metadata
LABEL maintainer="Agile Team"

# Set up workspace
RUN mkdir /app

WORKDIR /app
ADD app/app.py /app
ADD app/requirements.txt /app
ADD app/README.md /app

# Install packages
RUN pip install -U pip && \
    pip install --no-cache-dir -r requirements.txt \
    pip install curl

# Expose any ports the app is expecting in the environment
ENV PORT 5000
EXPOSE $PORT

# Service app
ENTRYPOINT [ "python" ]

CMD [ "app.py" ]

