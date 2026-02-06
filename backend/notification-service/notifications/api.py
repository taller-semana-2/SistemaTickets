from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Notification
from .serializers import NotificationSerializer


class NotificationViewSet(viewsets.ModelViewSet):
    queryset = Notification.objects.all().order_by('-sent_at')
    serializer_class = NotificationSerializer

    @action(detail=True, methods=['patch'], url_path='read')
    def read(self, request, pk=None):
        notification = self.get_object()
        notification.read = True
        notification.save(update_fields=['read'])
        return Response(status=status.HTTP_204_NO_CONTENT)
