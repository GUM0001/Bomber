import curlparser
import json
from urllib.parse import urlparse, parse_qsl


def process(text):
    text = text.replace("--compressed", "")

    result = curlparser.parse(text)

    parsed = urlparse(result.url)
    args = parse_qsl(parsed.query)

    json_data = {
        "method": result.method,
        "url": result.url,
        "headers": {},
    }

    if args:
        json_data["url"] = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        json_data["params"] = {k: v for k, v in args}

    if result.header:
        headers = result.header.copy()
        if "User-Agent" in headers:
            del headers["User-Agent"]
        json_data["headers"] = headers

    if result.data:
        content_type = result.header.get("Content-Type", "").split(";")[0]
        if content_type.startswith("application/x-www-form-urlencoded"):
            json_data["data"] = dict(parse_qsl(result.data))
        else:
            json_data["json"] = result.data

    print(json.dumps(json_data))


def main():
    print("Enter request data:")
    print("After entering data, press Ctrl+D (on Linux/Mac) or Ctrl+Z (on Windows) to finish input.")

    user_input = []
    try:
        while True:
            user_input.append(input())
    except EOFError:
        pass

    request_data = '\n'.join(user_input)
    process(request_data)


if __name__ == "__main__":
    main()
