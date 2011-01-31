import time
from tastypie.serializers import Serializer

class CustomJSONSerializer(Serializer):
  formats = ['json']
  content_types = {'json': 'application/json',}
