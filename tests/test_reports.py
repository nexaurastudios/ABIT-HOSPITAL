import pytest
from app import create_app
from app.config import TestConfig
from app.services.export_service import export_to_csv, export_to_excel, export_to_pdf

def test_export_to_csv():
    headers = ['ID', 'Name', 'Department']
    rows = [
        ['DOC-1', 'Arthur Vance', 'Cardiology'],
        ['DOC-2', 'Eleanor Vance', 'Neurology']
    ]
    csv_bytes = export_to_csv(headers, rows)
    assert b'Arthur Vance' in csv_bytes
    assert b'Cardiology' in csv_bytes

def test_export_to_excel():
    headers = ['ID', 'Name', 'Department']
    rows = [
        ['DOC-1', 'Arthur Vance', 'Cardiology'],
        ['DOC-2', 'Eleanor Vance', 'Neurology']
    ]
    excel_bytes = export_to_excel('Doctors', headers, rows)
    assert len(excel_bytes) > 100

def test_export_to_pdf():
    headers = ['ID', 'Name', 'Department']
    rows = [
        ['DOC-1', 'Arthur Vance', 'Cardiology'],
        ['DOC-2', 'Eleanor Vance', 'Neurology']
    ]
    pdf_bytes = export_to_pdf('Test Report', headers, rows)
    assert pdf_bytes.startswith(b'%PDF')

