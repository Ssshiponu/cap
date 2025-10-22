import json
from django.conf import settings

def metadata(request):
    path = request.path

    path = path if path.startswith('/') else '/' + path
    path = path if path.endswith('/') else path + '/'
    
    if path == '/' or path == '/en/':
        path = "/index/"
    
    with open(settings.METADATA_FILE) as f:
        data = json.load(f)

    try:
        metadata = data[path]
    except KeyError:
        metadata = data['/index/']
    
    return {"metadata": metadata}
