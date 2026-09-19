# Runnable examples

Self-contained examples that demonstrate common integration patterns against a
running server. They use only the standard library plus `httpx` (a dev
dependency), and synthetic data.

| Example | What it shows |
|---|---|
| [`quickstart_curl.sh`](quickstart_curl.sh) | The whole happy path with `curl`. |
| [`python_client.py`](python_client.py) | A typed Python client flow with `httpx`. |

## Running

Start the API first (see the README), then:

```bash
# curl
bash examples/quickstart_curl.sh

# python
python examples/python_client.py
```

Both default to `http://localhost:8000` and `admin`/`admin` (the development
bootstrap admin). Override with environment variables:
`OE_BASE_URL`, `OE_ADMIN_USERNAME`, `OE_ADMIN_PASSWORD`.