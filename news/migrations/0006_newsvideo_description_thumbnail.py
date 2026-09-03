from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('news', '0005_newsvideo_uploaded_video_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='newsvideo',
            name='description',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='newsvideo',
            name='thumbnail',
            field=models.ImageField(blank=True, null=True, upload_to='thumbnails/'),
        ),
    ]
