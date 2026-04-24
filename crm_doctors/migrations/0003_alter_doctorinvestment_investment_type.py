from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('crm_doctors', '0002_doctorpracticelocation_doctorvisit_visit_location'),
    ]

    operations = [
        migrations.AlterField(
            model_name='doctorinvestment',
            name='investment_type',
            field=models.CharField(
                choices=[
                    ('cash', 'Cash'),
                    ('tour', 'Tour and Accommodation'),
                    ('goods', 'Good Purchased'),
                    ('sponsorship', 'Sponsorship'),
                    ('lunch_dinner', 'Lunch / Dinner'),
                    ('other', 'Others'),
                ],
                max_length=15,
            ),
        ),
    ]
