from rest_framework import serializers
from littlebooks_API.models import Variables


class VariablesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Variables
        fields = ['id', 'name', 'value']
