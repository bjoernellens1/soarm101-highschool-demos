# Optional container image for the workshop API.
# NOTE: hardware access needs USB/serial passthrough, so run with --device flags:
#   docker build -f deploy/Dockerfile -t soarm-api .
#   docker run --rm -p 7860:7860 \
#       --device=/dev/ttyACM0 --device=/dev/ttyACM1 \
#       -e SOARM_API_TOKEN=changeme -e SOARM_HOST=0.0.0.0 \
#       -v $PWD/.calibration:/app/.calibration \
#       soarm-api
FROM python:3.12-slim

WORKDIR /app
COPY . .
RUN pip install --no-cache-dir -e '.[robot]'

ENV SOARM_HOST=0.0.0.0 SOARM_PORT=7860
EXPOSE 7860
CMD ["soarm-api"]
