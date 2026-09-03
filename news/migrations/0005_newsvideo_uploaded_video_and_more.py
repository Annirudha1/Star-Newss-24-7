from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('news', '0004_alter_newsvideo_created_at'),
    ]

    operations = [
        migrations.AlterField(
            model_name='newsvideo',
            name='youtube_link',
            field=models.URLField(blank=True),
        ),
        migrations.AddField(
            model_name='newsvideo',
            name='uploaded_video',
            field=models.FileField(blank=True, null=True, upload_to='videos/'),
        ),
    ]
