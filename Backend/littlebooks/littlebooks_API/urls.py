from rest_framework.routers import DefaultRouter
from .views.tiktok_token import TiktokViewSet

router = DefaultRouter()
router.register(r'tiktok', TiktokViewSet, basename='movies')

urlpatterns = router.urls