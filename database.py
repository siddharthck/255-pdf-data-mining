import sqlite3
import json
import pandas as pd
from datetime import datetime
from config import DB_PATH

def init_database():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            company_name TEXT,
            fiscal_year TEXT,
            upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            processed BOOLEAN DEFAULT FALSE
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS financial_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            doc_id INTEGER,
            metric_name TEXT,
            metric_value REAL,
            metric_unit TEXT,
            year TEXT,
            FOREIGN KEY (doc_id) REFERENCES documents (id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS risk_factors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            doc_id INTEGER,
            risk_category TEXT,
            risk_description TEXT,
            severity_level TEXT,
            FOREIGN KEY (doc_id) REFERENCES documents (id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS business_segments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            doc_id INTEGER,
            segment_name TEXT,
            segment_revenue REAL,
            segment_description TEXT,
            FOREIGN KEY (doc_id) REFERENCES documents (id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS extracted_text (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            doc_id INTEGER,
            section_name TEXT,
            content TEXT,
            FOREIGN KEY (doc_id) REFERENCES documents (id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS analysis_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            doc_id INTEGER,
            analysis_type TEXT,
            results TEXT,
            created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (doc_id) REFERENCES documents (id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS translations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            doc_id INTEGER,
            source_language TEXT,
            target_language TEXT,
            translated_content TEXT,
            section_name TEXT,
            FOREIGN KEY (doc_id) REFERENCES documents (id)
        )
    ''')
    
    conn.commit()
    conn.close()

def add_document(filename, company_name=None, fiscal_year=None):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO documents (filename, company_name, fiscal_year)
        VALUES (?, ?, ?)
    ''', (filename, company_name, fiscal_year))
    
    doc_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return doc_id

def update_document_processed(doc_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE documents SET processed = TRUE WHERE id = ?
    ''', (doc_id,))
    
    conn.commit()
    conn.close()

def save_financial_metrics(doc_id, metrics_data):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    for metric_name, value_info in metrics_data.items():
        if isinstance(value_info, dict):
            cursor.execute('''
                INSERT INTO financial_metrics (doc_id, metric_name, metric_value, metric_unit, year)
                VALUES (?, ?, ?, ?, ?)
            ''', (doc_id, metric_name, value_info.get('value'), value_info.get('unit'), value_info.get('year')))
        else:
            cursor.execute('''
                INSERT INTO financial_metrics (doc_id, metric_name, metric_value)
                VALUES (?, ?, ?)
            ''', (doc_id, metric_name, value_info))
    
    conn.commit()
    conn.close()

def save_risk_factors(doc_id, risk_data):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    for category, risks in risk_data.items():
        if isinstance(risks, list):
            for risk in risks:
                cursor.execute('''
                    INSERT INTO risk_factors (doc_id, risk_category, risk_description)
                    VALUES (?, ?, ?)
                ''', (doc_id, category, risk))
    
    conn.commit()
    conn.close()

def save_business_segments(doc_id, segments_data):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    for segment in segments_data:
        cursor.execute('''
            INSERT INTO business_segments (doc_id, segment_name, segment_revenue, segment_description)
            VALUES (?, ?, ?, ?)
        ''', (doc_id, segment.get('name'), segment.get('revenue'), segment.get('description')))
    
    conn.commit()
    conn.close()

def save_extracted_text(doc_id, section_name, content):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO extracted_text (doc_id, section_name, content)
        VALUES (?, ?, ?)
    ''', (doc_id, section_name, content))
    
    conn.commit()
    conn.close()

def save_analysis_results(doc_id, analysis_type, results):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    results_json = json.dumps(results) if isinstance(results, (dict, list)) else str(results)
    
    cursor.execute('''
        INSERT INTO analysis_results (doc_id, analysis_type, results)
        VALUES (?, ?, ?)
    ''', (doc_id, analysis_type, results_json))
    
    conn.commit()
    conn.close()

def get_document_info(doc_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM documents WHERE id = ?', (doc_id,))
    result = cursor.fetchone()
    
    conn.close()
    return result

def get_financial_metrics(doc_id):
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query('''
        SELECT metric_name, metric_value, metric_unit, year
        FROM financial_metrics WHERE doc_id = ?
    ''', conn, params=(doc_id,))
    
    conn.close()
    return df

def get_risk_factors(doc_id):
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query('''
        SELECT risk_category, risk_description, severity_level
        FROM risk_factors WHERE doc_id = ?
    ''', conn, params=(doc_id,))
    
    conn.close()
    return df

def get_business_segments(doc_id):
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query('''
        SELECT segment_name, segment_revenue, segment_description
        FROM business_segments WHERE doc_id = ?
    ''', conn, params=(doc_id,))
    
    conn.close()
    return df

def get_analysis_results(doc_id, analysis_type=None):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    if analysis_type:
        cursor.execute('''
            SELECT results FROM analysis_results 
            WHERE doc_id = ? AND analysis_type = ?
            ORDER BY created_date DESC LIMIT 1
        ''', (doc_id, analysis_type))
    else:
        cursor.execute('''
            SELECT analysis_type, results FROM analysis_results 
            WHERE doc_id = ? ORDER BY created_date DESC
        ''', (doc_id,))
    
    results = cursor.fetchall()
    conn.close()
    return results

def get_latest_document():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, filename, company_name, fiscal_year, processed
        FROM documents ORDER BY upload_date DESC LIMIT 1
    ''')
    
    result = cursor.fetchone()
    conn.close()
    return result

def save_translation(doc_id, source_lang, target_lang, translated_content, section_name):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO translations (doc_id, source_language, target_language, translated_content, section_name)
        VALUES (?, ?, ?, ?, ?)
    ''', (doc_id, source_lang, target_lang, translated_content, section_name))
    
    conn.commit()
    conn.close()

def get_translations(doc_id, target_language):
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query('''
        SELECT section_name, translated_content
        FROM translations WHERE doc_id = ? AND target_language = ?
    ''', conn, params=(doc_id, target_language))
    
    conn.close()
    return df

def clear_all_data():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    tables = ['documents', 'financial_metrics', 'risk_factors', 'business_segments', 
              'extracted_text', 'analysis_results', 'translations']
    
    for table in tables:
        cursor.execute(f'DELETE FROM {table}')
    
    conn.commit()
    conn.close()