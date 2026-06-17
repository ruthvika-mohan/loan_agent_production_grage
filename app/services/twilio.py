from xml.sax.saxutils import escape


def build_media_stream_twiml(public_base_url: str) -> str:
    websocket_url = public_base_url.replace("https://", "wss://").replace("http://", "ws://")
    stream_url = f"{websocket_url}/twilio/media"
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        "<Response>"
        "<Say>Connecting you to the loan status voice assistant.</Say>"
        "<Connect>"
        f'<Stream url="{escape(stream_url)}" />'
        "</Connect>"
        "</Response>"
    )

