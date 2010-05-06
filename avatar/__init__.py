from django.conf import settings

try:
    from PIL import Image
    dir(Image) # Placate PyFlakes
except ImportError:
    import Image

AUTO_GENERATE_AVATAR_SIZES = getattr(settings, 'AUTO_GENERATE_AVATAR_SIZES', (80,))
AVATAR_RESIZE_METHOD = getattr(settings, 'AVATAR_RESIZE_METHOD', Image.ANTIALIAS)
AVATAR_STORAGE_DIR = getattr(settings, 'AVATAR_STORAGE_DIR', 'avatars')
AVATAR_GRAVATAR_BACKUP = getattr(settings, 'AVATAR_GRAVATAR_BACKUP', True)
AVATAR_GRAVATAR_DEFAULT = getattr(settings, 'AVATAR_GRAVATAR_DEFAULT', None)
AVATAR_DEFAULT_URL = getattr(settings, 'AVATAR_DEFAULT_URL', 'avatar/img/default.jpg')
AVATAR_MAX_AVATARS_PER_USER = getattr(settings, 'AVATAR_MAX_AVATARS_PER_USER', 42)
AVATAR_MAX_SIZE = getattr(settings, 'AVATAR_MAX_SIZE', 1024 * 1024)
AVATAR_THUMB_FORMAT = getattr(settings, 'AVATAR_THUMB_FORMAT', "JPEG")
AVATAR_THUMB_QUALITY = getattr(settings, 'AVATAR_THUMB_QUALITY', 85)
AVATAR_HASH_FILENAMES = getattr(settings, 'AVATAR_HASH_FILENAMES', False)
AVATAR_HASH_USERDIRNAMES = getattr(settings, 'AVATAR_HASH_USERDIRNAMES', False)
AVATAR_ALLOWED_FILE_EXTS = getattr(settings, 'AVATAR_ALLOWED_FILE_EXTS', None)

from django.db.models import signals
from avatar.models import Avatar
from django.utils.translation import ugettext as _

notification = False
if 'notification' in settings.INSTALLED_APPS:
    from notification import models as notification

friends = False
if 'friends' in settings.INSTALLED_APPS:
    friends = True
    from friends.models import Friendship
    
relationships = False
if 'relationships' in settings.INSTALLED_APPS:
    relationships = True

def avatar_updated_callback(sender, instance, created, **kwargs):
    avatar = instance
    user = avatar.user
    if created:
        user.message_set.create(
                message=_("Successfully uploaded a new avatar."))
    elif avatar.primary:
        user.message_set.create(
                message=_("Successfully updated your avatar."))
    if avatar.primary:
        notification.send([user], "avatar_updated", {"user": user, "avatar": avatar})
        if friends:
            notification.send((x['friend'] for x in
                    Friendship.objects.friends_for_user(user)),
                "avatar_friend_updated", {"user": user, "avatar": avatar}
            )
        if relationships:
            notification.send(user.relationships.followers(),
                "avatar_friend_updated", {"user": user, "avatar": avatar}
            )
signals.post_save.connect(avatar_updated_callback, sender=Avatar)
        
def avatar_deleted_callback(sender, instance, **kwargs):
    user = instance.user
    user.message_set.create(
        message=_("Successfully deleted the requested avatars."))
signals.post_delete.connect(avatar_deleted_callback, sender=Avatar)

def create_default_thumbnails(instance=None, created=False, **kwargs):
    if created:
        for size in AUTO_GENERATE_AVATAR_SIZES:
            instance.create_thumbnail(size)
signals.post_save.connect(create_default_thumbnails, sender=Avatar)
