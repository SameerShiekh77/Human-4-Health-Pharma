import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('crm_doctors', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='DoctorPracticeLocation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('location_name', models.CharField(max_length=200)),
                ('location_type', models.CharField(choices=[('hospital', 'Hospital'), ('clinic', 'Clinic'), ('other', 'Other')], default='clinic', max_length=20)),
                ('address', models.CharField(blank=True, max_length=300, null=True)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('doctor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='practice_locations', to='crm_doctors.doctor')),
            ],
            options={
                'verbose_name': 'Doctor Practice Location',
                'verbose_name_plural': 'Doctor Practice Locations',
                'ordering': ['location_name'],
            },
        ),
        migrations.AddField(
            model_name='doctorvisit',
            name='visit_location',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='visits', to='crm_doctors.doctorpracticelocation'),
        ),
    ]
