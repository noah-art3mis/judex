import json
import logging
import sqlite3
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


def init_database(db_path: str):
    """Initialize the database with normalized tables"""
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()

        # Main processos table (keeping JSON fields for backward compatibility)
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
                assuntos TEXT, -- Keep as JSON for now
                -- Metadata
                html TEXT,
                error_message TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        # Normalized tables for JSON data

        # Partes table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS partes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                numero_unico TEXT NOT NULL,
                _index INTEGER,
                tipo TEXT,
                nome TEXT,
                FOREIGN KEY (numero_unico) REFERENCES processos(numero_unico) ON DELETE CASCADE
            )
        """
        )

        # Andamentos table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS andamentos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                numero_unico TEXT NOT NULL,
                index_num INTEGER,
                data TEXT,
                nome TEXT,
                complemento TEXT,
                julgador TEXT,
                FOREIGN KEY (numero_unico) REFERENCES processos(numero_unico) ON DELETE CASCADE
            )
        """
        )

        # Decisoes table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS decisoes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                numero_unico TEXT NOT NULL,
                index_num INTEGER,
                data TEXT,
                nome TEXT,
                julgador TEXT,
                complemento TEXT,
                link TEXT,
                FOREIGN KEY (numero_unico) REFERENCES processos(numero_unico) ON DELETE CASCADE
            )
        """
        )

        # Deslocamentos table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS deslocamentos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                numero_unico TEXT NOT NULL,
                index_num INTEGER,
                data_enviado TEXT,
                data_recebido TEXT,
                enviado_por TEXT,
                recebido_por TEXT,
                guia TEXT,
                FOREIGN KEY (numero_unico) REFERENCES processos(numero_unico) ON DELETE CASCADE
            )
        """
        )

        # Peticoes table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS peticoes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                numero_unico TEXT NOT NULL,
                index_num INTEGER,
                data TEXT,
                tipo TEXT,
                autor TEXT,
                recebido_data TEXT,
                recebido_por TEXT,
                FOREIGN KEY (numero_unico) REFERENCES processos(numero_unico) ON DELETE CASCADE
            )
        """
        )

        # Recursos table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS recursos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                numero_unico TEXT NOT NULL,
                index_num INTEGER,
                data TEXT,
                nome TEXT,
                julgador TEXT,
                complemento TEXT,
                autor TEXT,
                FOREIGN KEY (numero_unico) REFERENCES processos(numero_unico) ON DELETE CASCADE
            )
        """
        )

        # Pautas table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS pautas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                numero_unico TEXT NOT NULL,
                index_num INTEGER,
                data TEXT,
                nome TEXT,
                complemento TEXT,
                relator TEXT,
                FOREIGN KEY (numero_unico) REFERENCES processos(numero_unico) ON DELETE CASCADE
            )
        """
        )

        # Create indexes for main table
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_processos_incidente ON processos (numero_unico)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_processos_incidente_id ON processos (incidente)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_processos_processo_id ON processos (processo_id)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_processos_classe ON processos (classe)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_processos_created_at ON processos (created_at)"
        )

        # Create indexes for normalized tables
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_partes_numero_unico ON partes (numero_unico)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_andamentos_numero_unico ON andamentos (numero_unico)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_decisoes_numero_unico ON decisoes (numero_unico)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_deslocamentos_numero_unico ON deslocamentos (numero_unico)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_peticoes_numero_unico ON peticoes (numero_unico)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_recursos_numero_unico ON recursos (numero_unico)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_pautas_numero_unico ON pautas (numero_unico)"
        )

        conn.commit()


def processo_write(db_path: str, processo_data: dict[str, Any]) -> bool:
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()

            incidente = processo_data.get("incidente")
            numero_unico = processo_data.get("numero_unico")
            processo_id = processo_data.get("processo_id")
            if not incidente or not numero_unico or not processo_id:
                return False

            # Save main processo data
            cursor.execute(
                """
                INSERT OR REPLACE INTO processos (
                    numero_unico, incidente, processo_id, classe, tipo_processo, liminar, relator,
                    origem, origem_orgao, data_protocolo, autor1, assuntos,
                    html, error_message, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                    json.dumps(processo_data.get("assuntos"), ensure_ascii=False),
                    processo_data.get("html"),
                    processo_data.get("error_message"),
                    datetime.now().isoformat(),
                ),
            )

            # Save normalized data to separate tables
            _save_normalized_data(cursor, numero_unico, processo_data)

            conn.commit()
            logger.info(f"Saved processo data for {numero_unico}")
            return True

    except Exception as e:
        logger.error(f"Error saving case data: {str(e)}")
        return False


def _save_normalized_data(cursor, numero_unico: str, processo_data: dict[str, Any]):
    """Save JSON data to normalized tables"""

    # Clear existing data for this processo
    cursor.execute("DELETE FROM partes WHERE numero_unico = ?", (numero_unico,))
    cursor.execute("DELETE FROM andamentos WHERE numero_unico = ?", (numero_unico,))
    cursor.execute("DELETE FROM decisoes WHERE numero_unico = ?", (numero_unico,))
    cursor.execute("DELETE FROM deslocamentos WHERE numero_unico = ?", (numero_unico,))
    cursor.execute("DELETE FROM peticoes WHERE numero_unico = ?", (numero_unico,))
    cursor.execute("DELETE FROM recursos WHERE numero_unico = ?", (numero_unico,))
    cursor.execute("DELETE FROM pautas WHERE numero_unico = ?", (numero_unico,))

    # Save partes
    partes_data = processo_data.get("partes_total", [])
    for parte in partes_data:
        cursor.execute(
            "INSERT INTO partes (numero_unico, _index, tipo, nome) VALUES (?, ?, ?, ?)",
            (numero_unico, parte.get("_index"), parte.get("tipo"), parte.get("nome")),
        )

    # Save andamentos
    andamentos_data = processo_data.get("andamentos", [])
    for andamento in andamentos_data:
        cursor.execute(
            "INSERT INTO andamentos (numero_unico, index_num, data, nome, complemento, julgador) VALUES (?, ?, ?, ?, ?, ?)",
            (
                numero_unico,
                andamento.get("index"),
                andamento.get("data"),
                andamento.get("nome"),
                andamento.get("complemento"),
                andamento.get("julgador"),
            ),
        )

    # Save decisoes
    decisoes_data = processo_data.get("decisoes", [])
    for decisao in decisoes_data:
        cursor.execute(
            "INSERT INTO decisoes (numero_unico, index_num, data, nome, julgador, complemento, link) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                numero_unico,
                decisao.get("index"),
                decisao.get("data"),
                decisao.get("nome"),
                decisao.get("julgador"),
                decisao.get("complemento"),
                decisao.get("link"),
            ),
        )

    # Save deslocamentos
    deslocamentos_data = processo_data.get("deslocamentos", [])
    for deslocamento in deslocamentos_data:
        cursor.execute(
            "INSERT INTO deslocamentos (numero_unico, index_num, data_enviado, data_recebido, enviado_por, recebido_por, guia) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                numero_unico,
                deslocamento.get("index"),
                deslocamento.get("data_enviado"),
                deslocamento.get("data_recebido"),
                deslocamento.get("enviado_por"),
                deslocamento.get("recebido_por"),
                deslocamento.get("guia"),
            ),
        )

    # Save peticoes
    peticoes_data = processo_data.get("peticoes", [])
    for peticao in peticoes_data:
        cursor.execute(
            "INSERT INTO peticoes (numero_unico, index_num, data, tipo, autor, recebido_data, recebido_por) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                numero_unico,
                peticao.get("index"),
                peticao.get("data"),
                peticao.get("tipo"),
                peticao.get("autor"),
                peticao.get("recebido_data"),
                peticao.get("recebido_por"),
            ),
        )

    # Save recursos
    recursos_data = processo_data.get("recursos", [])
    for recurso in recursos_data:
        cursor.execute(
            "INSERT INTO recursos (numero_unico, index_num, data, nome, julgador, complemento, autor) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                numero_unico,
                recurso.get("index"),
                recurso.get("data"),
                recurso.get("nome"),
                recurso.get("julgador"),
                recurso.get("complemento"),
                recurso.get("autor"),
            ),
        )

    # Save pautas
    pautas_data = processo_data.get("pautas", [])
    for pauta in pautas_data:
        cursor.execute(
            "INSERT INTO pautas (numero_unico, index_num, data, nome, complemento, relator) VALUES (?, ?, ?, ?, ?, ?)",
            (
                numero_unico,
                pauta.get("index"),
                pauta.get("data"),
                pauta.get("nome"),
                pauta.get("complemento"),
                pauta.get("relator"),
            ),
        )


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


def processo_read(db_path: str, numero_unico: int) -> dict[str, Any]:
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()

            cursor.execute(
                "SELECT * FROM processos WHERE numero_unico = ?", (numero_unico,)
            )
            return cursor.fetchone() or {}

    except Exception as e:
        logger.error(f"Error getting processo data: {str(e)}")
        return {}


def processo_read_all(db_path: str) -> list[dict[str, Any]]:
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM processos")
            return cursor.fetchall() or []
    except Exception as e:
        logger.error(f"Error getting all processos: {str(e)}")
        return []


def has_recent_data(
    db_path: str, processo_id: int, classe: str, max_age_hours: int = 24
) -> bool:
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
                (processo_id, classe),
            )

            count = cursor.fetchone()[0]
            return count > 0

    except Exception as e:
        logger.error(f"Error checking recent data: {str(e)}")
        return False


def get_existing_processo_ids(
    db_path: str, classe: str, max_age_hours: int = 24
) -> set[int]:
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
                (classe,),
            )

            results = cursor.fetchall()
            return {row[0] for row in results}

    except Exception as e:
        logger.error(f"Error getting existing processo IDs: {str(e)}")
        return set()


def get_failed_processo_ids(
    db_path: str, classe: str, max_age_hours: int = 24
) -> set[int]:
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
                (classe,),
            )

            results = cursor.fetchall()
            return {row[0] for row in results}

    except Exception as e:
        logger.error(f"Error getting failed processo IDs: {str(e)}")
        return set()


# Helper functions for querying normalized data


def get_processo_andamentos(db_path: str, numero_unico: str) -> list[dict[str, Any]]:
    """Get all andamentos for a specific processo"""
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM andamentos WHERE numero_unico = ? ORDER BY index_num DESC",
                (numero_unico,),
            )
            columns = [description[0] for description in cursor.description]
            return [dict(zip(columns, row, strict=True)) for row in cursor.fetchall()]
    except Exception as e:
        logger.error(f"Error getting andamentos: {str(e)}")
        return []


def get_processo_partes(db_path: str, numero_unico: str) -> list[dict[str, Any]]:
    """Get all partes for a specific processo"""
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM partes WHERE numero_unico = ? ORDER BY _index",
                (numero_unico,),
            )
            columns = [description[0] for description in cursor.description]
            return [dict(zip(columns, row, strict=True)) for row in cursor.fetchall()]
    except Exception as e:
        logger.error(f"Error getting partes: {str(e)}")
        return []


def get_processo_decisoes(db_path: str, numero_unico: str) -> list[dict[str, Any]]:
    """Get all decisoes for a specific processo"""
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM decisoes WHERE numero_unico = ? ORDER BY index_num DESC",
                (numero_unico,),
            )
            columns = [description[0] for description in cursor.description]
            return [dict(zip(columns, row, strict=True)) for row in cursor.fetchall()]
    except Exception as e:
        logger.error(f"Error getting decisoes: {str(e)}")
        return []


def get_processo_deslocamentos(db_path: str, numero_unico: str) -> list[dict[str, Any]]:
    """Get all deslocamentos for a specific processo"""
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM deslocamentos WHERE numero_unico = ? ORDER BY index_num DESC",
                (numero_unico,),
            )
            columns = [description[0] for description in cursor.description]
            return [dict(zip(columns, row, strict=True)) for row in cursor.fetchall()]
    except Exception as e:
        logger.error(f"Error getting deslocamentos: {str(e)}")
        return []


def get_processo_peticoes(db_path: str, numero_unico: str) -> list[dict[str, Any]]:
    """Get all peticoes for a specific processo"""
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM peticoes WHERE numero_unico = ? ORDER BY index_num DESC",
                (numero_unico,),
            )
            columns = [description[0] for description in cursor.description]
            return [dict(zip(columns, row, strict=True)) for row in cursor.fetchall()]
    except Exception as e:
        logger.error(f"Error getting peticoes: {str(e)}")
        return []


def get_processo_recursos(db_path: str, numero_unico: str) -> list[dict[str, Any]]:
    """Get all recursos for a specific processo"""
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM recursos WHERE numero_unico = ? ORDER BY index_num DESC",
                (numero_unico,),
            )
            columns = [description[0] for description in cursor.description]
            return [dict(zip(columns, row, strict=True)) for row in cursor.fetchall()]
    except Exception as e:
        logger.error(f"Error getting recursos: {str(e)}")
        return []


def get_processo_pautas(db_path: str, numero_unico: str) -> list[dict[str, Any]]:
    """Get all pautas for a specific processo"""
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM pautas WHERE numero_unico = ? ORDER BY index_num DESC",
                (numero_unico,),
            )
            columns = [description[0] for description in cursor.description]
            return [dict(zip(columns, row, strict=True)) for row in cursor.fetchall()]
    except Exception as e:
        logger.error(f"Error getting pautas: {str(e)}")
        return []


def get_complete_processo(db_path: str, numero_unico: str) -> dict[str, Any]:
    """Get complete processo data including all normalized tables"""
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()

            # Get main processo data
            cursor.execute(
                "SELECT * FROM processos WHERE numero_unico = ?", (numero_unico,)
            )
            processo_row = cursor.fetchone()
            if not processo_row:
                return {}

            # Convert to dict
            columns = [description[0] for description in cursor.description]
            processo_data = dict(zip(columns, processo_row, strict=True))

            # Add normalized data
            processo_data["andamentos"] = get_processo_andamentos(db_path, numero_unico)
            processo_data["partes"] = get_processo_partes(db_path, numero_unico)
            processo_data["decisoes"] = get_processo_decisoes(db_path, numero_unico)
            processo_data["deslocamentos"] = get_processo_deslocamentos(
                db_path, numero_unico
            )
            processo_data["peticoes"] = get_processo_peticoes(db_path, numero_unico)
            processo_data["recursos"] = get_processo_recursos(db_path, numero_unico)
            processo_data["pautas"] = get_processo_pautas(db_path, numero_unico)

            return processo_data

    except Exception as e:
        logger.error(f"Error getting complete processo data: {str(e)}")
        return {}
