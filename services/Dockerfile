FROM python:3.11-slim
WORKDIR /app
COPY services/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt
COPY services/ps_sha_infinity_core.py /app/ps_sha_infinity_core.py
COPY services/ps_sha_infinity_api.py /app/ps_sha_infinity_api.py
ENV PS_SHA_INFINITY_TOKEN=change-me-dev
COPY services/ui /app/ui
ENV PS_SHA_INFINITY_SIGNING_SECRET=dev-signing-secret
ENV PS_SHA_INFINITY_SALT=dev-salt

EXPOSE 8000
CMD ["uvicorn", "ps_sha_infinity_api:app", "--host", "0.0.0.0", "--port", "8000"]
