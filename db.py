import sqlite3
import json
from datetime import datetime


def init_database(db_path: str):
    """Initialize the database with a single main table"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Single main table with JSON fields
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            incidente INTEGER UNIQUE NOT NULL,
            processo_id INTEGER UNIQUE NOT NULL,
            classe TEXT,
            classe_extenso TEXT,
            nome_processo TEXT,
            tipo_processo TEXT,
            liminar TEXT,
            origem TEXT,
            relator TEXT,
            autor1 TEXT,
            data_protocolo TEXT,
            origem_orgao TEXT,
            
            -- JSON fields for complex data
            partes_total TEXT, -- JSON array of parties
            lista_assuntos TEXT, -- JSON array of subjects
            andamentos_lista TEXT, -- JSON array of proceedings
            decisoes TEXT, -- JSON array of decisions
            deslocamentos_lista TEXT, -- JSON array of displacements
            
            -- Processing status
            main_page_loaded BOOLEAN DEFAULT FALSE,
            partes_loaded BOOLEAN DEFAULT FALSE,
            andamentos_loaded BOOLEAN DEFAULT FALSE,
            decisoes_loaded BOOLEAN DEFAULT FALSE,
            deslocamentos_loaded BOOLEAN DEFAULT FALSE,
            assuntos_loaded BOOLEAN DEFAULT FALSE,
            
            -- Metadata
            error_message TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create indexes for better performance
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_cases_incidente ON cases (incidente)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_cases_classe ON cases (classe)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_cases_created_at ON cases (created_at)')
    
    conn.commit()
    conn.close()

def save_case_data(db_path: str, case_data: dict[str, any]) -> bool:
    """Save complete case data to database"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        incidente = case_data.get('incidente')
        if not incidente:
            return False
        
        # Prepare JSON fields
        partes_json = json.dumps(case_data.get('partes_total', []), ensure_ascii=False)
        assuntos_json = json.dumps(case_data.get('lista_assuntos', []), ensure_ascii=False)
        andamentos_json = json.dumps(case_data.get('andamentos_lista', []), ensure_ascii=False)
        decisoes_json = json.dumps(case_data.get('decisões', []), ensure_ascii=False)
        deslocamentos_json = json.dumps(case_data.get('deslocamentos_lista', []), ensure_ascii=False)
        
        # Determine which fields were loaded
        main_page_loaded = bool(case_data.get('classe') or case_data.get('nome_processo'))
        partes_loaded = bool(case_data.get('partes_total'))
        andamentos_loaded = bool(case_data.get('andamentos_lista'))
        decisoes_loaded = bool(case_data.get('decisões'))
        deslocamentos_loaded = bool(case_data.get('deslocamentos_lista'))
        assuntos_loaded = bool(case_data.get('lista_assuntos'))
        
        cursor.execute('''
            INSERT OR REPLACE INTO cases (
                incidente, classe, classe_extenso, nome_processo, tipo_processo,
                liminar, origem, relator, autor1, data_protocolo, origem_orgao,
                partes_total, lista_assuntos, andamentos_lista, decisoes, deslocamentos_lista,
                main_page_loaded, partes_loaded, andamentos_loaded, decisoes_loaded, 
                deslocamentos_loaded, assuntos_loaded, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            incidente,
            case_data.get('classe'),
            case_data.get('classe_extenso'),
            case_data.get('nome_processo'),
            case_data.get('tipo_processo'),
            case_data.get('liminar'),
            case_data.get('origem'),
            case_data.get('relator'),
            case_data.get('autor1'),
            case_data.get('data_protocolo'),
            case_data.get('origem_orgao'),
            partes_json,
            assuntos_json,
            andamentos_json,
            decisoes_json,
            deslocamentos_json,
            main_page_loaded,
            partes_loaded,
            andamentos_loaded,
            decisoes_loaded,
            deslocamentos_loaded,
            assuntos_loaded,
            datetime.now().isoformat()
        ))
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        print(f"Error saving case data: {str(e)}")
        if 'conn' in locals():
            conn.close()
        return False

def mark_error(db_path: str, incidente: int, error_message: str):
    """Mark a case as having an error"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE cases 
            SET error_message = ?, updated_at = ?
            WHERE incidente = ?
        ''', (error_message, datetime.now().isoformat(), incidente))
        
        conn.commit()
        conn.close()
        
    except Exception as e:
        print(f"Error marking error: {str(e)}")