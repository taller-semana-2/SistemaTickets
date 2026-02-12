"""
users/serializers.py

📋 CAPA DE PRESENTACIÓN - Serialización

🎯 PROPÓSITO:
Transforma datos entre JSON (HTTP) y objetos Python.

📐 ESTRUCTURA:
- Un serializer por cada operación de API
- Valida INPUT desde el cliente
- Formatea OUTPUT hacia el cliente
- NO contiene lógica de negocio

✅ EJEMPLO de lo que DEBE ir aquí:
    from rest_framework import serializers
    
    class CreateUserSerializer(serializers.Serializer):
        '''Serializer para crear un usuario (INPUT)'''
        email = serializers.EmailField(required=True)
        username = serializers.CharField(min_length=3, max_length=50, required=True)
        password = serializers.CharField(min_length=8, write_only=True, required=True)
    
    class UserSerializer(serializers.Serializer):
        '''Serializer para representar un usuario (OUTPUT)'''
        id = serializers.CharField(read_only=True)
        email = serializers.EmailField()
        username = serializers.CharField()
        is_active = serializers.BooleanField()
        
        # NO incluimos password en el output por seguridad
    
    class DeactivateUserSerializer(serializers.Serializer):
        '''Serializer para desactivar un usuario'''
        reason = serializers.CharField(max_length=200, required=True)

💡 Los serializers son el "traductor" entre HTTP/JSON y tu aplicación.
   Hacen validaciones básicas, NO validaciones de negocio (esas van en el dominio).
"""
