import json
import logging
import sqlite3
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


def init_database(db_path: str):
    """Initialize the database with a single main table"""
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()

        # Single main table with JSON fields
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS processos (
                -- ids
                numero_unico TEXT PRIMARY KEY,
                incidente INTEGER UNIQUE,
                processo_id INTEGER UNIQUE,
                -- info
                classe TEXT CHECK (classe IN ('AC', 'ACO', 'ADC', 'ADI', 'ADO', 'ADPF', 'AI', 'AImp', 'AO', 'AOE', 'AP', 'AR', 'ARE', 'AS', 'CC', 'Cm', 'EI', 'EL', 'EP', 'Ext', 'HC', 'HD', 'IF', 'Inq', 'MI', 'MS', 'PADM', 'Pet', 'PPE', 'PSV', 'RC', 'Rcl', 'RE', 'RHC', 'RHD', 'RMI', 'RMS', 'RvC', 'SE', 'SIRDR', 'SL', 'SS', 'STA', 'STP', 'TPA')),
                tipo_processo TEXT CHECK (tipo_processo IN ('Físico', 'Eletrônico')),
                liminar INT CHECK (liminar IN (0, 1)),
                relator TEXT,
                origem TEXT,
                origem_orgao TEXT,
                data_protocolo TEXT,
                autor1 TEXT,
                -- JSON fields
                partes TEXT, -- JSON
                assuntos TEXT, -- JSON
                andamentos TEXT, -- JSON
                decisoes TEXT, -- JSON
                deslocamentos TEXT, --JSON
                peticoes TEXT, -- JSON
                recursos TEXT, -- JSON
                pautas TEXT, -- JSON
                -- Metadata
                html TEXT,
                error_message TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_processos_incidente ON processos (numero_unico)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_processos_incidente ON processos (incidente)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_processos_incidente ON processos (processo_id)"
        )
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_processos_classe ON processos (classe)")

        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_processos_created_at ON processos (created_at)"
        )

        conn.commit()


def save_processo_data(db_path: str, processo_data: dict[str, Any]) -> bool:
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()

            incidente = processo_data.get("incidente")
            numero_unico = processo_data.get("numero_unico")
            processo_id = processo_data.get("processo_id")
            if not incidente or not numero_unico or not processo_id:
                return False

            cursor.execute(
                """
                INSERT OR REPLACE INTO processos (
                    numero_unico, incidente, processo_id, classe, tipo_processo, liminar, relator,
                    origem, origem_orgao, data_protocolo, autor1,
                    partes, assuntos, andamentos, decisoes, deslocamentos, peticoes, recursos, pautas,
                    html, error_message, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    processo_data.get("numero_unico"),
                    processo_data.get("incidente"),
                    processo_data.get("processo_id"),
                    processo_data.get("classe"),
                    processo_data.get("tipo_processo"),
                    processo_data.get("liminar"),
                    processo_data.get("relator"),
                    processo_data.get("origem"),
                    processo_data.get("origem_orgao"),
                    processo_data.get("data_protocolo"),
                    processo_data.get("autor1"),
                    json.dumps(processo_data.get("partes_total", []), ensure_ascii=False),
                    json.dumps(processo_data.get("assuntos"), ensure_ascii=False),
                    json.dumps(processo_data.get("andamentos"), ensure_ascii=False),
                    json.dumps(processo_data.get("decisoes"), ensure_ascii=False),
                    json.dumps(processo_data.get("deslocamentos"), ensure_ascii=False),
                    json.dumps(processo_data.get("peticoes"), ensure_ascii=False),
                    json.dumps(processo_data.get("recursos"), ensure_ascii=False),
                    json.dumps(processo_data.get("pautas"), ensure_ascii=False),
                    processo_data.get("html"),
                    processo_data.get("error_message"),
                    datetime.now().isoformat(),
                ),
            )

            conn.commit()
            logger.info(f"Saved processo data for {numero_unico}")
            return True

    except Exception as e:
        logger.error(f"Error saving case data: {str(e)}")
        return False


def mark_error(db_path: str, numero_unico: int, error_message: str) -> bool:
    """Mark a case as having an error"""

    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                UPDATE processos
                SET error_message = ?,
                updated_at = ?
                WHERE numero_unico = ?
            """,
                (error_message, str(datetime.now().isoformat()), numero_unico),
            )

            conn.commit()
            return True
    except Exception as e:
        logger.error(f"Error marking error: {str(e)}")
        return False


def get_processo_data(db_path: str, numero_unico: int) -> dict[str, Any]:
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM processos WHERE numero_unico = ?", (numero_unico,))
            return cursor.fetchone() or {}

    except Exception as e:
        logger.error(f"Error getting processo data: {str(e)}")
        return {}


def get_all_processos(db_path: str) -> list[dict[str, Any]]:
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM processos")
            return cursor.fetchall() or []
    except Exception as e:
        logger.error(f"Error getting all processos: {str(e)}")
        return []


def has_recent_data(db_path: str, processo_id: int, classe: str, max_age_hours: int = 24) -> bool:
    """Check if we have recent data for a processo_id and classe combination"""
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()

            # Check for recent data (within max_age_hours)
            cursor.execute(
                f"""
                SELECT COUNT(*) FROM processos
                WHERE processo_id = ? AND classe = ?
                AND created_at > datetime('now', '-{max_age_hours} hours')
                AND error_message IS NULL
                """,
                (processo_id, classe)
            )

            count = cursor.fetchone()[0]
            return count > 0

    except Exception as e:
        logger.error(f"Error checking recent data: {str(e)}")
        return False


def get_existing_processo_ids(db_path: str, classe: str, max_age_hours: int = 24) -> set[int]:
    """Get all processo_ids that already have recent data for a given classe"""
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()

            cursor.execute(
                f"""
                SELECT processo_id FROM processos
                WHERE classe = ?
                AND created_at > datetime('now', '-{max_age_hours} hours')
                AND error_message IS NULL
                """,
                (classe,)
            )

            results = cursor.fetchall()
            return {row[0] for row in results}

    except Exception as e:
        logger.error(f"Error getting existing processo IDs: {str(e)}")
        return set()


def get_failed_processo_ids(db_path: str, classe: str, max_age_hours: int = 24) -> set[int]:
    """Get all processo_ids that failed recently and should be retried"""
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()

            cursor.execute(
                f"""
                SELECT processo_id FROM processos
                WHERE classe = ?
                AND created_at > datetime('now', '-{max_age_hours} hours')
                AND error_message IS NOT NULL
                """,
                (classe,)
            )

            results = cursor.fetchall()
            return {row[0] for row in results}

    except Exception as e:
        logger.error(f"Error getting failed processo IDs: {str(e)}")
        return set()
