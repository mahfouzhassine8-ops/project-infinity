"""Fixed read-only directory proof inside the remaining original card deadline."""
import json
import socket
import time


def read(device,media,deadline):
    if media not in ('movie','tv'):raise ValueError('Exact saved media required')
    method='Files.GetDirectory'
    params=dict(directory='plugin://script.infinity.uirepair/?action=continue&media='+media,
        media='video',properties=['resume'])
    device.guard((method,json.dumps(params)))
    request=dict(jsonrpc='2.0',id=731,method=method,params=params)
    def remaining():
        value=deadline-time.monotonic()
        if value<=0:raise TimeoutError('Original20sec saved-card proof deadline exceeded')
        return value
    with socket.create_connection(('127.0.0.1',19090),timeout=remaining()) as connection:
        connection.sendall(json.dumps(request).encode())
        pending=b'';decoder=json.JSONDecoder()
        while True:
            connection.settimeout(remaining())
            chunk=connection.recv(65536)
            if not chunk:raise RuntimeError('Actual native resume proof connection closed')
            pending+=chunk
            if len(pending)>1024*1024:raise RuntimeError('Oversized actual native resume proof')
            try:response,end=decoder.raw_decode(pending.decode('utf-8').lstrip())
            except (UnicodeDecodeError,ValueError):continue
            if response.get('id')!=731 or 'error' in response:raise RuntimeError('Actual native resume proof refused')
            remaining()
            return response['result']
