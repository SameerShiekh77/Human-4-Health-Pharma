from __future__ import annotations

import csv
import io
from datetime import datetime

from django.contrib import messages
from core.auth_utils import crm_access_required
from django.http import Http404, HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse

from .config import DATA_MODELS, ImportErrorRow, export_value, parse_row
from .forms import DataUploadForm
from crm_doctors.models import DoctorPracticeLocation, DoctorVisit
from crm_stores.models import MedicalStore


PENDING_SESSION_PREFIX = 'crm_data_tools_pending_'


def _get_model_config(model_key: str):
    config = DATA_MODELS.get(model_key)
    if not config:
        raise Http404('Unknown data set')
    return config


def _pending_session_key(model_key: str) -> str:
    return f'{PENDING_SESSION_PREFIX}{model_key}'


def _format_filename(prefix: str, suffix: str = 'csv') -> str:
    return f'{prefix}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.{suffix}'


def _build_preview_rows(staged_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    return [
        {
            'row_number': index,
            'raw': row['raw'],
            'errors': row['errors'],
        }
        for index, row in enumerate(staged_rows, start=1)
    ]


@crm_access_required
def export_csv(request, model_key: str):
    config = _get_model_config(model_key)
    model = config['model']

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{_format_filename(config["file_prefix"])}"'

    writer = csv.writer(response)
    writer.writerow([column.header for column in config['export_columns']])

    queryset = model.objects.all()
    for obj in queryset:
        writer.writerow([export_value(column, obj) for column in config['export_columns']])

    return response


@crm_access_required
def sample_csv(request, model_key: str):
    config = _get_model_config(model_key)

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{config["file_prefix"]}_sample.csv"'

    writer = csv.writer(response)
    headers = [column.header for column in config['import_columns']]
    writer.writerow(headers)
    writer.writerow([config['sample_row'].get(header, '') for header in headers])
    return response


@crm_access_required
def import_upload(request, model_key: str):
    config = _get_model_config(model_key)
    session_key = _pending_session_key(model_key)
    form = DataUploadForm(request.POST or None, request.FILES or None)

    if request.method == 'POST' and request.POST.get('confirm') == '1':
        staged = request.session.get(session_key)
        if not staged:
            messages.error(request, 'No staged import was found. Please upload the file again.')
            return redirect(reverse(config['list_url']))

        staged_rows = staged.get('rows', [])
        if any(row['errors'] for row in staged_rows):
            messages.error(request, 'Resolve the preview errors before confirming the import.')
            return render(
                request,
                'crm/data_tools/import_preview.html',
                {
                    'config': config,
                    'form': DataUploadForm(),
                    'preview_rows': _build_preview_rows(staged_rows),
                    'row_errors': sum(1 for row in staged_rows if row['errors']),
                    'total_rows': len(staged_rows),
                    'has_errors': True,
                    'sample_url': reverse('crm_data_tools:sample', args=[model_key]),
                    'export_url': reverse('crm_data_tools:export', args=[model_key]),
                    'import_url': reverse('crm_data_tools:import', args=[model_key]),
                    'model_key': model_key,
                },
            )

        created = 0
        updated = 0
        model = config['model']
        lookup_fn = config['lookup']

        for staged_row in staged_rows:
            raw_row = staged_row['raw']
            cleaned, errors = parse_row(config['import_columns'], raw_row)
            if errors:
                continue

            lookup_data = lookup_fn(raw_row)
            lookup_data = {key: value for key, value in lookup_data.items() if value not in (None, '')}

            instance = model.objects.filter(**lookup_data).first() if lookup_data else None
            if instance:
                updated += 1
            else:
                instance = model()
                created += 1

            m2m_assignments = {}
            special_visit_location_name = raw_row.get('Visit Location') or raw_row.get('Hospital / Clinic Name')

            for field_name, value in cleaned.items():
                if field_name in {'visit_location_name'}:
                    continue
                try:
                    model._meta.get_field(field_name)
                except Exception:
                    continue

                field = model._meta.get_field(field_name)
                if field.many_to_many:
                    m2m_assignments[field_name] = value
                    continue

                setattr(instance, field_name, value)

            if model is DoctorVisit and special_visit_location_name:
                location = DoctorPracticeLocation.objects.filter(
                    doctor=cleaned['doctor'],
                    location_name=special_visit_location_name,
                ).first()
                if not location:
                    location = DoctorPracticeLocation.objects.create(
                        doctor=cleaned['doctor'],
                        location_name=special_visit_location_name,
                        location_type='clinic',
                        address='',
                        is_active=True,
                    )
                instance.visit_location = location
                instance.hospital_clinic_name = special_visit_location_name

            if model is MedicalStore and 'linked_doctors' in cleaned:
                m2m_assignments['linked_doctors'] = cleaned['linked_doctors']

            instance.save()

            for field_name, value in m2m_assignments.items():
                getattr(instance, field_name).set(value)

        request.session.pop(session_key, None)
        messages.success(request, f'Imported {created + updated} row(s): {created} created, {updated} updated.')
        return redirect(reverse(config['list_url']))

    if request.method == 'POST' and form.is_valid():
        upload = request.FILES['data_file']
        try:
            data_stream = io.TextIOWrapper(upload.file, encoding='utf-8-sig')
            reader = csv.DictReader(data_stream)
            expected_headers = [column.header for column in config['import_columns']]
            actual_headers = reader.fieldnames or []

            if actual_headers != expected_headers:
                messages.error(
                    request,
                    'CSV headers do not match the sample file. Download the sample file and keep the same column order.'
                )
                return render(request, 'crm/data_tools/import_form.html', {
                    'config': config,
                    'form': form,
                    'sample_url': reverse('crm_data_tools:sample', args=[model_key]),
                    'export_url': reverse('crm_data_tools:export', args=[model_key]),
                    'import_url': reverse('crm_data_tools:import', args=[model_key]),
                    'model_key': model_key,
                })

            staged_rows = []
            for row in reader:
                staged_rows.append({
                    'raw': dict(row),
                    'errors': parse_row(config['import_columns'], row)[1],
                })

            request.session[session_key] = {
                'rows': staged_rows,
                'model_key': model_key,
            }
            request.session.modified = True

            return render(request, 'crm/data_tools/import_preview.html', {
                'config': config,
                'form': DataUploadForm(),
                'preview_rows': _build_preview_rows(staged_rows),
                'row_errors': sum(1 for row in staged_rows if row['errors']),
                'total_rows': len(staged_rows),
                'has_errors': any(row['errors'] for row in staged_rows),
                'sample_url': reverse('crm_data_tools:sample', args=[model_key]),
                'export_url': reverse('crm_data_tools:export', args=[model_key]),
                'import_url': reverse('crm_data_tools:import', args=[model_key]),
                'model_key': model_key,
            })

        except ImportErrorRow as exc:
            messages.error(request, str(exc))
        except Exception as exc:
            messages.error(request, f'Could not read the file: {exc}')

    return render(request, 'crm/data_tools/import_form.html', {
        'config': config,
        'form': form,
        'sample_url': reverse('crm_data_tools:sample', args=[model_key]),
        'export_url': reverse('crm_data_tools:export', args=[model_key]),
        'import_url': reverse('crm_data_tools:import', args=[model_key]),
        'model_key': model_key,
    })
