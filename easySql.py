#!/usr/bin/env python3
"""
easySql - Interactive SQL Learning Application
A PyQt6-based educational tool for learning SQL with SQLite
Supports English and Spanish, includes beginner and advanced lessons
"""

import sys
import sqlite3
from datetime import datetime
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QPushButton, QTextEdit, QTableView, QLabel,
    QComboBox, QMessageBox, QScrollArea, QCheckBox, QSplitter,
    QMenuBar, QMenu
)
from PyQt6.QtCore import Qt, QAbstractTableModel, pyqtSignal
from PyQt6.QtGui import QAction


# ===========================
# Database Manager
# ===========================

class DatabaseManager:
    """Manages SQLite database operations, schema, and data"""

    def __init__(self, db_path="easysql_learning.db"):
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        self.connect()
        self.initialize_database()

    def connect(self):
        """Establish database connection"""
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()

    def initialize_database(self):
        """Create tables and populate with sample data"""
        # Create main learning tables
        self.cursor.executescript("""
            CREATE TABLE IF NOT EXISTS students (
                student_id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT UNIQUE,
                age INTEGER,
                country TEXT
            );

            CREATE TABLE IF NOT EXISTS courses (
                course_id INTEGER PRIMARY KEY,
                course_name TEXT NOT NULL,
                instructor TEXT,
                credits INTEGER
            );

            CREATE TABLE IF NOT EXISTS enrollments (
                enrollment_id INTEGER PRIMARY KEY,
                student_id INTEGER,
                course_id INTEGER,
                enrollment_date TEXT,
                grade REAL,
                FOREIGN KEY (student_id) REFERENCES students(student_id),
                FOREIGN KEY (course_id) REFERENCES courses(course_id)
            );

            CREATE TABLE IF NOT EXISTS lesson_progress (
                lesson_id TEXT PRIMARY KEY,
                completed INTEGER DEFAULT 0,
                completed_at TEXT
            );

            CREATE TABLE IF NOT EXISTS query_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query_text TEXT NOT NULL,
                executed_at TEXT NOT NULL,
                success INTEGER,
                error_message TEXT
            );
        """)

        # Check if sample data exists in all tables
        self.cursor.execute("SELECT COUNT(*) FROM students")
        students_count = self.cursor.fetchone()[0]

        self.cursor.execute("SELECT COUNT(*) FROM courses")
        courses_count = self.cursor.fetchone()[0]

        self.cursor.execute("SELECT COUNT(*) FROM enrollments")
        enrollments_count = self.cursor.fetchone()[0]

        # Only populate if all tables are empty
        if students_count == 0 and courses_count == 0 and enrollments_count == 0:
            self._populate_sample_data()

        self.conn.commit()

    def _populate_sample_data(self):
        """Insert sample data for learning"""
        # Students
        students_data = [
            (1, 'Alice Johnson', 'alice@email.com', 20, 'USA'),
            (2, 'Bob Smith', 'bob@email.com', 22, 'Canada'),
            (3, 'Carlos García', 'carlos@email.com', 21, 'Spain'),
            (4, 'Diana Lee', 'diana@email.com', 19, 'South Korea'),
            (5, 'Elena Rodríguez', 'elena@email.com', 23, 'Mexico'),
            (6, 'Frank Miller', 'frank@email.com', 20, 'UK'),
            (7, 'Gabriela Silva', 'gabi@email.com', 22, 'Brazil'),
            (8, 'Hassan Ahmed', 'hassan@email.com', 21, 'Egypt')
        ]

        # Courses
        courses_data = [
            (1, 'Introduction to Programming', 'Dr. Smith', 3),
            (2, 'Database Systems', 'Prof. Johnson', 4),
            (3, 'Web Development', 'Dr. García', 3),
            (4, 'Data Structures', 'Prof. Lee', 4),
            (5, 'Machine Learning', 'Dr. Chen', 3),
            (6, 'Computer Networks', 'Prof. Williams', 3)
        ]

        # Enrollments
        enrollments_data = [
            (1, 1, 1, '2024-01-15', 3.8),
            (2, 1, 2, '2024-01-15', 3.5),
            (3, 2, 1, '2024-01-16', 3.2),
            (4, 2, 3, '2024-01-16', 3.9),
            (5, 3, 2, '2024-01-17', 4.0),
            (6, 3, 4, '2024-01-17', 3.7),
            (7, 4, 1, '2024-01-18', 3.6),
            (8, 4, 5, '2024-01-18', 3.8),
            (9, 5, 3, '2024-01-19', 3.4),
            (10, 5, 4, '2024-01-19', 3.9),
            (11, 6, 2, '2024-01-20', 3.3),
            (12, 6, 6, '2024-01-20', 3.7),
            (13, 7, 1, '2024-01-21', 3.5),
            (14, 8, 5, '2024-01-22', 3.6)
        ]

        self.cursor.executemany(
            "INSERT OR IGNORE INTO students VALUES (?, ?, ?, ?, ?)", students_data
        )
        self.cursor.executemany(
            "INSERT OR IGNORE INTO courses VALUES (?, ?, ?, ?)", courses_data
        )
        self.cursor.executemany(
            "INSERT OR IGNORE INTO enrollments VALUES (?, ?, ?, ?, ?)", enrollments_data
        )

        self.conn.commit()

    def execute_query(self, query):
        """Execute SQL query and return results"""
        try:
            self.cursor.execute(query)

            # Check if SELECT and fetch results BEFORE committing
            if query.strip().upper().startswith('SELECT') and self.cursor.description:
                columns = [description[0] for description in self.cursor.description]
                rows = self.cursor.fetchall()
                self._save_query_history(query, success=True)
                return {'success': True, 'columns': columns, 'rows': rows}
            else:
                # Only commit for non-SELECT queries (INSERT, UPDATE, DELETE, etc.)
                self.conn.commit()
                self._save_query_history(query, success=True)
                return {'success': True, 'message': f'Query executed successfully. Rows affected: {self.cursor.rowcount}'}

        except sqlite3.Error as e:
            self._save_query_history(query, success=False, error=str(e))
            return {'success': False, 'error': str(e)}

    def _save_query_history(self, query, success, error=None):
        """Save query to history table"""
        timestamp = datetime.now().isoformat()
        self.cursor.execute(
            "INSERT INTO query_history (query_text, executed_at, success, error_message) VALUES (?, ?, ?, ?)",
            (query, timestamp, 1 if success else 0, error)
        )
        self.conn.commit()

    def get_query_history(self, limit=50):
        """Retrieve recent query history"""
        self.cursor.execute(
            "SELECT query_text, executed_at, success, error_message FROM query_history ORDER BY id DESC LIMIT ?",
            (limit,)
        )
        return self.cursor.fetchall()

    def get_table_data(self, table_name):
        """Get all data from a specific table"""
        try:
            self.cursor.execute(f"SELECT * FROM {table_name}")
            columns = [description[0] for description in self.cursor.description]
            rows = self.cursor.fetchall()
            return {'success': True, 'columns': columns, 'rows': rows}
        except sqlite3.Error as e:
            return {'success': False, 'error': str(e)}

    def get_table_names(self):
        """Get list of user tables (excluding system tables)"""
        self.cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' AND name NOT IN ('lesson_progress', 'query_history')"
        )
        return [row[0] for row in self.cursor.fetchall()]

    def mark_lesson_complete(self, lesson_id):
        """Mark a lesson as completed"""
        timestamp = datetime.now().isoformat()
        self.cursor.execute(
            "INSERT OR REPLACE INTO lesson_progress (lesson_id, completed, completed_at) VALUES (?, 1, ?)",
            (lesson_id, timestamp)
        )
        self.conn.commit()

    def is_lesson_complete(self, lesson_id):
        """Check if lesson is completed"""
        self.cursor.execute(
            "SELECT completed FROM lesson_progress WHERE lesson_id = ?",
            (lesson_id,)
        )
        result = self.cursor.fetchone()
        return result[0] == 1 if result else False

    def reset_lesson_progress(self):
        """Reset all lesson progress without affecting database content"""
        self.cursor.execute("DELETE FROM lesson_progress")
        self.conn.commit()

    def reset_database(self):
        """Drop all tables and reinitialize with fresh data"""
        self.cursor.executescript("""
            DROP TABLE IF EXISTS students;
            DROP TABLE IF EXISTS courses;
            DROP TABLE IF EXISTS enrollments;
            DROP TABLE IF EXISTS lesson_progress;
        """)
        # Keep query history
        self.conn.commit()
        self.initialize_database()

    def get_table_schema(self, table_name):
        """Get column information for a table using PRAGMA table_info"""
        try:
            self.cursor.execute(f"PRAGMA table_info({table_name})")
            columns_info = self.cursor.fetchall()
            # Returns list of tuples: (cid, name, type, notnull, dflt_value, pk)
            schema = []
            for col in columns_info:
                schema.append({
                    'cid': col[0],
                    'name': col[1],
                    'type': col[2],
                    'notnull': col[3],
                    'default': col[4],
                    'pk': col[5]
                })
            return {'success': True, 'schema': schema}
        except sqlite3.Error as e:
            return {'success': False, 'error': str(e)}

    def get_primary_key(self, table_name):
        """Get primary key column name(s) for a table"""
        schema_result = self.get_table_schema(table_name)
        if not schema_result['success']:
            return schema_result

        pk_columns = [col['name'] for col in schema_result['schema'] if col['pk'] > 0]

        if not pk_columns:
            return {'success': False, 'error': 'No primary key found'}

        # Return first PK column (most tables have single column PKs)
        return {'success': True, 'pk_column': pk_columns[0], 'pk_columns': pk_columns}

    def update_cell(self, table_name, pk_column, pk_value, column_name, new_value):
        """Update a single cell value and return the generated SQL"""
        try:
            # Generate UPDATE SQL
            sql = f"UPDATE {table_name} SET {column_name} = ? WHERE {pk_column} = ?"

            # Execute the update
            self.cursor.execute(sql, (new_value, pk_value))
            self.conn.commit()

            # Save to query history with actual values for learning
            display_sql = f"UPDATE {table_name} SET {column_name} = '{new_value}' WHERE {pk_column} = {pk_value}"
            self._save_query_history(display_sql, success=True)

            return {
                'success': True,
                'sql': display_sql,
                'message': f'Cell updated successfully'
            }
        except sqlite3.Error as e:
            error_sql = f"UPDATE {table_name} SET {column_name} = '{new_value}' WHERE {pk_column} = {pk_value}"
            self._save_query_history(error_sql, success=False, error=str(e))
            return {'success': False, 'error': str(e), 'sql': error_sql}

    def insert_row(self, table_name, column_values):
        """Insert a new row and return the generated SQL"""
        try:
            # Get schema to identify columns (excluding auto-increment PKs)
            schema_result = self.get_table_schema(table_name)
            if not schema_result['success']:
                return schema_result

            columns = [col['name'] for col in schema_result['schema']]
            placeholders = ', '.join(['?' for _ in columns])
            columns_str = ', '.join(columns)

            # Generate INSERT SQL
            sql = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})"

            # Execute the insert
            self.cursor.execute(sql, column_values)
            self.conn.commit()

            # Save to query history
            values_str = ', '.join([f"'{v}'" if v is not None else 'NULL' for v in column_values])
            display_sql = f"INSERT INTO {table_name} ({columns_str}) VALUES ({values_str})"
            self._save_query_history(display_sql, success=True)

            return {
                'success': True,
                'sql': display_sql,
                'message': f'Row inserted successfully',
                'rowid': self.cursor.lastrowid
            }
        except sqlite3.Error as e:
            return {'success': False, 'error': str(e)}

    def delete_row(self, table_name, pk_column, pk_value):
        """Delete a row and return the generated SQL"""
        try:
            # Generate DELETE SQL
            sql = f"DELETE FROM {table_name} WHERE {pk_column} = ?"

            # Execute the delete
            self.cursor.execute(sql, (pk_value,))
            self.conn.commit()

            # Save to query history
            display_sql = f"DELETE FROM {table_name} WHERE {pk_column} = {pk_value}"
            self._save_query_history(display_sql, success=True)

            return {
                'success': True,
                'sql': display_sql,
                'message': f'Row deleted successfully'
            }
        except sqlite3.Error as e:
            display_sql = f"DELETE FROM {table_name} WHERE {pk_column} = {pk_value}"
            self._save_query_history(display_sql, success=False, error=str(e))
            return {'success': False, 'error': str(e), 'sql': display_sql}


# ===========================
# Language Manager
# ===========================

class LanguageManager:
    """Manages multilingual translations (English and Spanish)"""

    def __init__(self):
        self.current_language = 'en'
        self.translations = {
            'en': {
                # Menu and general
                'app_title': 'easySql - Interactive SQL Learning',
                'language': 'Language',
                'database': 'Database',
                'reset_db': 'Reset Database',
                'reset_confirm': 'Are you sure you want to reset the database? All changes will be lost.',
                'reset_success': 'Database has been reset successfully!',
                'reset_progress': 'Reset Lesson Progress',
                'reset_progress_confirm': 'Are you sure you want to reset all lesson progress? This will clear your completion history but keep the database intact.',
                'reset_progress_success': 'Lesson progress has been reset successfully!',

                # Tabs
                'tab_beginner': 'Beginner Lessons',
                'tab_advanced': 'Advanced/Dangerous',
                'tab_viewer': 'Table Viewer',
                'tab_console': 'SQL Console',

                # Beginner lessons tab
                'select_lesson': 'Select a lesson:',
                'run_example': 'Run Example',
                'mark_complete': 'Mark as Complete',
                'completed': '✓ Completed',

                # Advanced tab
                'danger_warning': '⚠️ Warning: Dangerous Commands',
                'danger_desc': 'These commands can delete or destroy data. Use with caution!',
                'confirm_danger': 'Are you sure you want to execute this dangerous command?',

                # Table viewer
                'select_table': 'Select table:',
                'refresh': 'Refresh',
                'no_data': 'No data available',

                # SQL Console
                'console_title': 'SQL Console - Write and execute your own queries',
                'query_placeholder': 'Enter your SQL query here...',
                'execute_query': 'Execute Query',
                'clear_console': 'Clear',
                'query_history': 'Query History',
                'success': 'Success',
                'error': 'Error',

                # Messages
                'query_executed': 'Query executed successfully!',
                'rows_affected': 'Rows affected:',
            },
            'es': {
                # Menú y general
                'app_title': 'easySql - Aprendizaje Interactivo de SQL',
                'language': 'Idioma',
                'database': 'Base de Datos',
                'reset_db': 'Reiniciar Base de Datos',
                'reset_confirm': '¿Está seguro de que desea reiniciar la base de datos? Todos los cambios se perderán.',
                'reset_success': '¡La base de datos se ha reiniciado exitosamente!',
                'reset_progress': 'Reiniciar Progreso de Lecciones',
                'reset_progress_confirm': '¿Está seguro de que desea reiniciar todo el progreso de las lecciones? Esto borrará su historial de completado pero mantendrá la base de datos intacta.',
                'reset_progress_success': '¡El progreso de las lecciones se ha reiniciado exitosamente!',

                # Pestañas
                'tab_beginner': 'Lecciones Básicas',
                'tab_advanced': 'Avanzado/Peligroso',
                'tab_viewer': 'Visor de Tablas',
                'tab_console': 'Consola SQL',

                # Pestaña de lecciones básicas
                'select_lesson': 'Seleccione una lección:',
                'run_example': 'Ejecutar Ejemplo',
                'mark_complete': 'Marcar como Completada',
                'completed': '✓ Completada',

                # Pestaña avanzada
                'danger_warning': '⚠️ Advertencia: Comandos Peligrosos',
                'danger_desc': '¡Estos comandos pueden eliminar o destruir datos. Use con precaución!',
                'confirm_danger': '¿Está seguro de que desea ejecutar este comando peligroso?',

                # Visor de tablas
                'select_table': 'Seleccionar tabla:',
                'refresh': 'Actualizar',
                'no_data': 'No hay datos disponibles',

                # Consola SQL
                'console_title': 'Consola SQL - Escriba y ejecute sus propias consultas',
                'query_placeholder': 'Ingrese su consulta SQL aquí...',
                'execute_query': 'Ejecutar Consulta',
                'clear_console': 'Limpiar',
                'query_history': 'Historial de Consultas',
                'success': 'Éxito',
                'error': 'Error',

                # Mensajes
                'query_executed': '¡Consulta ejecutada exitosamente!',
                'rows_affected': 'Filas afectadas:',
            }
        }

    def set_language(self, lang_code):
        """Set current language"""
        if lang_code in self.translations:
            self.current_language = lang_code

    def get(self, key):
        """Get translation for key"""
        return self.translations[self.current_language].get(key, key)


# ===========================
# Lesson Manager
# ===========================

class LessonManager:
    """Stores and manages SQL lessons"""

    def __init__(self):
        self.beginner_lessons = self._create_beginner_lessons()
        self.advanced_lessons = self._create_advanced_lessons()

    def _create_beginner_lessons(self):
        """Define beginner-friendly SQL lessons"""
        return {
            'SELECT_1': {
                'id': 'SELECT_1',
                'title_en': '1. SELECT - Basic Query',
                'title_es': '1. SELECT - Consulta Básica',
                'description_en': 'The SELECT statement retrieves data from a database table. Use * to select all columns, or specify column names.',
                'description_es': 'La sentencia SELECT recupera datos de una tabla de base de datos. Use * para seleccionar todas las columnas, o especifique nombres de columnas.',
                'sql': 'SELECT * FROM students;'
            },
            'SELECT_2': {
                'id': 'SELECT_2',
                'title_en': '2. SELECT - Specific Columns',
                'title_es': '2. SELECT - Columnas Específicas',
                'description_en': 'You can select specific columns instead of all columns. This is more efficient for large tables.',
                'description_es': 'Puede seleccionar columnas específicas en lugar de todas las columnas. Esto es más eficiente para tablas grandes.',
                'sql': 'SELECT name, email, country FROM students;'
            },
            'WHERE_1': {
                'id': 'WHERE_1',
                'title_en': '3. WHERE - Filter Results',
                'title_es': '3. WHERE - Filtrar Resultados',
                'description_en': 'The WHERE clause filters records based on conditions. Only rows that match the condition are returned.',
                'description_es': 'La cláusula WHERE filtra registros basados en condiciones. Solo se devuelven las filas que coinciden con la condición.',
                'sql': "SELECT name, age, country FROM students WHERE age >= 21;"
            },
            'WHERE_2': {
                'id': 'WHERE_2',
                'title_en': '4. WHERE - Multiple Conditions',
                'title_es': '4. WHERE - Múltiples Condiciones',
                'description_en': 'Use AND, OR operators to combine multiple conditions in WHERE clause.',
                'description_es': 'Use los operadores AND, OR para combinar múltiples condiciones en la cláusula WHERE.',
                'sql': "SELECT name, country FROM students WHERE age > 20 AND country = 'USA';"
            },
            'ORDER_1': {
                'id': 'ORDER_1',
                'title_en': '5. ORDER BY - Sort Results',
                'title_es': '5. ORDER BY - Ordenar Resultados',
                'description_en': 'ORDER BY sorts query results. Use ASC (ascending, default) or DESC (descending).',
                'description_es': 'ORDER BY ordena los resultados de la consulta. Use ASC (ascendente, predeterminado) o DESC (descendente).',
                'sql': 'SELECT name, age FROM students ORDER BY age DESC;'
            },
            'JOIN_1': {
                'id': 'JOIN_1',
                'title_en': '6. INNER JOIN - Combine Tables',
                'title_es': '6. INNER JOIN - Combinar Tablas',
                'description_en': 'INNER JOIN combines rows from two or more tables based on a related column. It returns only matching rows from both tables.',
                'description_es': 'INNER JOIN combina filas de dos o más tablas basándose en una columna relacionada. Devuelve solo las filas coincidentes de ambas tablas.',
                'sql': '''SELECT students.name, courses.course_name, enrollments.grade
FROM enrollments
INNER JOIN students ON enrollments.student_id = students.student_id
INNER JOIN courses ON enrollments.course_id = courses.course_id;'''
            },
            'JOIN_2': {
                'id': 'JOIN_2',
                'title_en': '6a. INNER JOIN - Simple Two Tables',
                'title_es': '6a. INNER JOIN - Dos Tablas Simples',
                'description_en': 'INNER JOIN with just two tables. This shows students and their enrollment dates, excluding students without enrollments.',
                'description_es': 'INNER JOIN con solo dos tablas. Esto muestra estudiantes y sus fechas de inscripción, excluyendo estudiantes sin inscripciones.',
                'sql': '''SELECT students.name, students.country, enrollments.enrollment_date
FROM students
INNER JOIN enrollments ON students.student_id = enrollments.student_id
ORDER BY enrollments.enrollment_date;'''
            },
            'JOIN_3': {
                'id': 'JOIN_3',
                'title_en': '6b. INNER JOIN - With WHERE Filter',
                'title_es': '6b. INNER JOIN - Con Filtro WHERE',
                'description_en': 'INNER JOIN combined with WHERE clause to filter results. This shows only students with grades above 3.5.',
                'description_es': 'INNER JOIN combinado con cláusula WHERE para filtrar resultados. Esto muestra solo estudiantes con calificaciones superiores a 3.5.',
                'sql': '''SELECT students.name, courses.course_name, enrollments.grade
FROM enrollments
INNER JOIN students ON enrollments.student_id = students.student_id
INNER JOIN courses ON enrollments.course_id = courses.course_id
WHERE enrollments.grade > 3.5
ORDER BY enrollments.grade DESC;'''
            },
            'JOIN_4': {
                'id': 'JOIN_4',
                'title_en': '6c. LEFT JOIN - All Students',
                'title_es': '6c. LEFT JOIN - Todos los Estudiantes',
                'description_en': 'LEFT JOIN returns ALL rows from the left table (students), even if there are no matches in the right table (enrollments). Unmatched rows show NULL.',
                'description_es': 'LEFT JOIN devuelve TODAS las filas de la tabla izquierda (estudiantes), incluso si no hay coincidencias en la tabla derecha (inscripciones). Las filas sin coincidencia muestran NULL.',
                'sql': '''SELECT students.name, students.country, courses.course_name, enrollments.grade
FROM students
LEFT JOIN enrollments ON students.student_id = enrollments.student_id
LEFT JOIN courses ON enrollments.course_id = courses.course_id
ORDER BY students.name;'''
            },
            'JOIN_5': {
                'id': 'JOIN_5',
                'title_en': '6d. LEFT JOIN - All Courses',
                'title_es': '6d. LEFT JOIN - Todos los Cursos',
                'description_en': 'LEFT JOIN showing all courses and their enrollments. Courses with no students enrolled will show NULL in student columns.',
                'description_es': 'LEFT JOIN mostrando todos los cursos y sus inscripciones. Los cursos sin estudiantes inscritos mostrarán NULL en las columnas de estudiantes.',
                'sql': '''SELECT courses.course_name, courses.instructor, students.name, enrollments.grade
FROM courses
LEFT JOIN enrollments ON courses.course_id = enrollments.course_id
LEFT JOIN students ON enrollments.student_id = students.student_id
ORDER BY courses.course_name;'''
            },
            'JOIN_6': {
                'id': 'JOIN_6',
                'title_en': '6e. LEFT JOIN - Find Unmatched Rows',
                'title_es': '6e. LEFT JOIN - Encontrar Filas Sin Coincidencia',
                'description_en': 'LEFT JOIN with IS NULL finds rows in the left table that have NO match in the right table. This finds students not enrolled in any course.',
                'description_es': 'LEFT JOIN con IS NULL encuentra filas en la tabla izquierda que NO tienen coincidencia en la tabla derecha. Esto encuentra estudiantes no inscritos en ningún curso.',
                'sql': '''SELECT students.name, students.email, students.country
FROM students
LEFT JOIN enrollments ON students.student_id = enrollments.student_id
WHERE enrollments.enrollment_id IS NULL;'''
            },
            'JOIN_7': {
                'id': 'JOIN_7',
                'title_en': '6f. RIGHT JOIN - All Courses',
                'title_es': '6f. RIGHT JOIN - Todos los Cursos',
                'description_en': 'RIGHT JOIN returns ALL rows from the right table (courses), even if there are no matches in the left table. Note: SQLite does not support RIGHT JOIN, so this uses LEFT JOIN with reversed table order.',
                'description_es': 'RIGHT JOIN devuelve TODAS las filas de la tabla derecha (cursos), incluso si no hay coincidencias en la tabla izquierda. Nota: SQLite no soporta RIGHT JOIN, así que esto usa LEFT JOIN con orden de tablas invertido.',
                'sql': '''SELECT courses.course_name, courses.credits, students.name
FROM courses
LEFT JOIN enrollments ON courses.course_id = enrollments.course_id
LEFT JOIN students ON enrollments.student_id = students.student_id
ORDER BY courses.course_name;'''
            },
            'JOIN_8': {
                'id': 'JOIN_8',
                'title_en': '6g. Understanding JOIN Types',
                'title_es': '6g. Entendiendo Tipos de JOIN',
                'description_en': 'This query demonstrates the difference between INNER JOIN and LEFT JOIN. INNER JOIN shows only enrolled students, LEFT JOIN shows all students.',
                'description_es': 'Esta consulta demuestra la diferencia entre INNER JOIN y LEFT JOIN. INNER JOIN muestra solo estudiantes inscritos, LEFT JOIN muestra todos los estudiantes.',
                'sql': '''SELECT
    COUNT(DISTINCT students.student_id) as total_students,
    COUNT(DISTINCT enrollments.enrollment_id) as total_enrollments
FROM students
LEFT JOIN enrollments ON students.student_id = enrollments.student_id;'''
            },
            'CASE_1': {
                'id': 'CASE_1',
                'title_en': '6h. CASE - Grade Categories',
                'title_es': '6h. CASE - Categorías de Calificaciones',
                'description_en': 'CASE creates conditional logic in SQL. This categorizes grades as Excellent (>3.5), Good (3.0-3.5), Pass (2.0-3.0), or Fail (<2.0).',
                'description_es': 'CASE crea lógica condicional en SQL. Esto categoriza calificaciones como Excelente (>3.5), Bueno (3.0-3.5), Aprobado (2.0-3.0), o Reprobado (<2.0).',
                'sql': '''SELECT
    students.name,
    courses.course_name,
    enrollments.grade,
    CASE
        WHEN enrollments.grade >= 3.5 THEN 'Excellent'
        WHEN enrollments.grade >= 3.0 THEN 'Good'
        WHEN enrollments.grade >= 2.0 THEN 'Pass'
        ELSE 'Fail'
    END as grade_category
FROM enrollments
INNER JOIN students ON enrollments.student_id = students.student_id
INNER JOIN courses ON enrollments.course_id = courses.course_id
ORDER BY enrollments.grade DESC;'''
            },
            'CASE_2': {
                'id': 'CASE_2',
                'title_en': '6i. CASE - Multiple Conditions',
                'title_es': '6i. CASE - Múltiples Condiciones',
                'description_en': 'CASE with multiple conditions. This categorizes students by age groups: Youth (<21), Young Adult (21-25), Adult (>25).',
                'description_es': 'CASE con múltiples condiciones. Esto categoriza estudiantes por grupos de edad: Joven (<21), Adulto Joven (21-25), Adulto (>25).',
                'sql': '''SELECT
    name,
    age,
    country,
    CASE
        WHEN age < 21 THEN 'Youth'
        WHEN age BETWEEN 21 AND 25 THEN 'Young Adult'
        ELSE 'Adult'
    END as age_group,
    CASE
        WHEN country IN ('USA', 'Canada', 'Mexico') THEN 'North America'
        WHEN country IN ('Spain', 'France', 'Germany') THEN 'Europe'
        WHEN country IN ('China', 'Japan', 'Korea') THEN 'Asia'
        ELSE 'Other'
    END as region
FROM students
ORDER BY age;'''
            },
            'CASE_3': {
                'id': 'CASE_3',
                'title_en': '6j. CASE with JOIN - Complex Logic',
                'title_es': '6j. CASE con JOIN - Lógica Compleja',
                'description_en': 'CASE combined with JOIN for complex logic. This shows student performance and credit earned based on grade.',
                'description_es': 'CASE combinado con JOIN para lógica compleja. Esto muestra rendimiento estudiantil y créditos obtenidos basados en calificación.',
                'sql': '''SELECT
    students.name,
    courses.course_name,
    courses.credits,
    enrollments.grade,
    CASE
        WHEN enrollments.grade >= 2.0 THEN courses.credits
        ELSE 0
    END as credits_earned,
    CASE
        WHEN enrollments.grade >= 3.5 THEN 'Honor Roll'
        WHEN enrollments.grade >= 2.0 THEN 'Passed'
        ELSE 'Failed'
    END as status
FROM enrollments
INNER JOIN students ON enrollments.student_id = students.student_id
INNER JOIN courses ON enrollments.course_id = courses.course_id
ORDER BY students.name, enrollments.grade DESC;'''
            },
            'CASE_4': {
                'id': 'CASE_4',
                'title_en': '6k. CASE with GROUP BY - Aggregation',
                'title_es': '6k. CASE con GROUP BY - Agregación',
                'description_en': 'CASE with GROUP BY and aggregation functions. This counts how many students achieved each grade level per course.',
                'description_es': 'CASE con GROUP BY y funciones de agregación. Esto cuenta cuántos estudiantes alcanzaron cada nivel de calificación por curso.',
                'sql': '''SELECT
    courses.course_name,
    COUNT(*) as total_students,
    SUM(CASE WHEN enrollments.grade >= 3.5 THEN 1 ELSE 0 END) as excellent_count,
    SUM(CASE WHEN enrollments.grade >= 3.0 AND enrollments.grade < 3.5 THEN 1 ELSE 0 END) as good_count,
    SUM(CASE WHEN enrollments.grade >= 2.0 AND enrollments.grade < 3.0 THEN 1 ELSE 0 END) as pass_count,
    SUM(CASE WHEN enrollments.grade < 2.0 THEN 1 ELSE 0 END) as fail_count,
    ROUND(AVG(enrollments.grade), 2) as avg_grade
FROM enrollments
INNER JOIN courses ON enrollments.course_id = courses.course_id
GROUP BY courses.course_name
ORDER BY avg_grade DESC;'''
            },
            'INSERT_1': {
                'id': 'INSERT_1',
                'title_en': '7. INSERT - Add New Data',
                'title_es': '7. INSERT - Agregar Nuevos Datos',
                'description_en': 'INSERT adds new rows to a table. Specify column names and values.',
                'description_es': 'INSERT agrega nuevas filas a una tabla. Especifique nombres de columnas y valores.',
                'sql': "INSERT OR REPLACE INTO students (student_id, name, email, age, country) VALUES (9, 'New Student', 'new@email.com', 20, 'USA');"
            },
            'UPDATE_1': {
                'id': 'UPDATE_1',
                'title_en': '8. UPDATE - Modify Data',
                'title_es': '8. UPDATE - Modificar Datos',
                'description_en': 'UPDATE modifies existing data. Always use WHERE to specify which rows to update!',
                'description_es': 'UPDATE modifica datos existentes. ¡Siempre use WHERE para especificar qué filas actualizar!',
                'sql': "UPDATE students SET age = 21 WHERE name = 'New Student';"
            },
            'DELETE_1': {
                'id': 'DELETE_1',
                'title_en': '9. DELETE - Remove Data',
                'title_es': '9. DELETE - Eliminar Datos',
                'description_en': 'DELETE removes rows from a table. Always use WHERE to specify which rows to delete!',
                'description_es': 'DELETE elimina filas de una tabla. ¡Siempre use WHERE para especificar qué filas eliminar!',
                'sql': "DELETE FROM students WHERE name = 'New Student';"
            },
            'CREATE_1': {
                'id': 'CREATE_1',
                'title_en': '10. CREATE TABLE - Make New Table',
                'title_es': '10. CREATE TABLE - Crear Nueva Tabla',
                'description_en': 'CREATE TABLE creates a new table with specified columns and data types.',
                'description_es': 'CREATE TABLE crea una nueva tabla con columnas y tipos de datos especificados.',
                'sql': '''CREATE TABLE IF NOT EXISTS test_table (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    created_at TEXT
);'''
            }
        }

    def _create_advanced_lessons(self):
        """Define advanced/dangerous SQL lessons"""
        return {
            'DROP_1': {
                'id': 'DROP_1',
                'title_en': 'DROP TABLE - Delete Entire Table',
                'title_es': 'DROP TABLE - Eliminar Tabla Completa',
                'description_en': '⚠️ DANGER: DROP TABLE permanently deletes an entire table and all its data. This cannot be undone! Use only when you are absolutely sure.',
                'description_es': '⚠️ PELIGRO: DROP TABLE elimina permanentemente una tabla completa y todos sus datos. ¡Esto no se puede deshacer! Use solo cuando esté absolutamente seguro.',
                'sql': 'DROP TABLE IF EXISTS test_table;',
                'dangerous': True
            },
            'DELETE_ALL': {
                'id': 'DELETE_ALL',
                'title_en': 'DELETE - Remove All Rows',
                'title_es': 'DELETE - Eliminar Todas las Filas',
                'description_en': '⚠️ DANGER: DELETE without WHERE removes ALL rows from a table. The table structure remains but all data is gone.',
                'description_es': '⚠️ PELIGRO: DELETE sin WHERE elimina TODAS las filas de una tabla. La estructura de la tabla permanece pero todos los datos desaparecen.',
                'sql': 'DELETE FROM enrollments;',
                'dangerous': True
            },
            'DROP_STUDENTS': {
                'id': 'DROP_STUDENTS',
                'title_en': 'DROP TABLE students',
                'title_es': 'DROP TABLE students',
                'description_en': '⚠️ DANGER: This will completely remove the students table. All student data will be permanently lost!',
                'description_es': '⚠️ PELIGRO: Esto eliminará completamente la tabla students. ¡Todos los datos de estudiantes se perderán permanentemente!',
                'sql': 'DROP TABLE IF EXISTS students;',
                'dangerous': True
            },
            'DROP_COURSES': {
                'id': 'DROP_COURSES',
                'title_en': 'DROP TABLE courses',
                'title_es': 'DROP TABLE courses',
                'description_en': '⚠️ DANGER: This will completely remove the courses table and all course information.',
                'description_es': '⚠️ PELIGRO: Esto eliminará completamente la tabla courses y toda la información de cursos.',
                'sql': 'DROP TABLE IF EXISTS courses;',
                'dangerous': True
            }
        }


# ===========================
# Table Model for QTableView
# ===========================

class TableModel(QAbstractTableModel):
    """Custom table model for displaying SQL query results with editing support"""

    # Signal emitted when SQL is generated (for display purposes)
    sql_generated = pyqtSignal(str)

    def __init__(self, data=None, columns=None, db=None, table_name=None):
        super().__init__()
        # Convert tuples to lists for mutability
        self._data = [list(row) for row in (data or [])]
        self._columns = columns or []
        self._db = db  # Database manager reference
        self._table_name = table_name  # Current table name
        self._pk_column = None  # Primary key column name
        self._pk_index = None  # Primary key column index
        self._schema = {}  # Column schema information

    def rowCount(self, parent=None):
        return len(self._data)

    def columnCount(self, parent=None):
        return len(self._columns)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole or role == Qt.ItemDataRole.EditRole:
            value = self._data[index.row()][index.column()]
            return str(value) if value is not None else ''
        return None

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                return self._columns[section]
            else:
                return str(section + 1)
        return None

    def flags(self, index):
        """Make cells editable if we have database connection and table info"""
        if self._db and self._table_name and self._pk_column is not None:
            # Don't allow editing the primary key column if it's auto-increment
            if index.column() == self._pk_index:
                pk_info = self._schema.get(self._pk_column, {})
                if pk_info.get('type', '').upper() == 'INTEGER' and pk_info.get('pk') == 1:
                    # Auto-increment INTEGER PRIMARY KEY - read only
                    return Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable

            return Qt.ItemFlag.ItemIsEditable | Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable
        else:
            # Read-only mode (for SQL console results, lesson results, etc.)
            return Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable

    def setData(self, index, value, role=Qt.ItemDataRole.EditRole):
        """Handle cell edits with immediate database update"""
        if role != Qt.ItemDataRole.EditRole:
            return False

        if not self._db or not self._table_name or self._pk_column is None:
            return False

        row = index.row()
        col = index.column()
        old_value = self._data[row][col]
        column_name = self._columns[col]

        # Don't update if value hasn't changed
        if str(old_value) == str(value):
            return False

        # Get primary key value for WHERE clause
        pk_value = self._data[row][self._pk_index]

        # Validate data type
        column_schema = self._schema.get(column_name, {})
        validated_value, error = self._validate_value(value, column_schema)

        if error:
            # Emit signal with error for display
            self.sql_generated.emit(f"ERROR: {error}")
            return False

        # Update database
        result = self._db.update_cell(
            self._table_name,
            self._pk_column,
            pk_value,
            column_name,
            validated_value
        )

        if result['success']:
            # Update local data
            self._data[row][col] = validated_value
            self.dataChanged.emit(index, index, [Qt.ItemDataRole.DisplayRole])

            # Emit SQL for display
            self.sql_generated.emit(result['sql'])
            return True
        else:
            # Emit error
            self.sql_generated.emit(f"ERROR: {result.get('error', 'Unknown error')}")
            return False

    def _validate_value(self, value, column_schema):
        """Validate value based on column type"""
        # Handle empty string
        if value == '' or value is None:
            if column_schema.get('notnull'):
                return None, "Column cannot be NULL"
            return None, None

        column_type = column_schema.get('type', 'TEXT').upper()

        # INTEGER validation
        if 'INT' in column_type:
            try:
                return int(value), None
            except ValueError:
                return None, f"Invalid INTEGER value: '{value}'"

        # REAL/FLOAT validation
        elif 'REAL' in column_type or 'FLOAT' in column_type or 'DOUBLE' in column_type:
            try:
                return float(value), None
            except ValueError:
                return None, f"Invalid REAL/FLOAT value: '{value}'"

        # TEXT - accept anything
        else:
            return str(value), None

    def update_data(self, data, columns):
        """Update table data (read-only mode)"""
        self.beginResetModel()
        self._data = [list(row) for row in data]
        self._columns = columns
        # Clear editing metadata
        self._table_name = None
        self._pk_column = None
        self._pk_index = None
        self._schema = {}
        self.endResetModel()

    def set_editable(self, db, table_name):
        """Enable editing mode for this table"""
        self._db = db
        self._table_name = table_name

        # Get primary key
        pk_result = db.get_primary_key(table_name)
        if pk_result['success']:
            self._pk_column = pk_result['pk_column']
            # Find PK column index
            try:
                self._pk_index = self._columns.index(self._pk_column)
            except ValueError:
                self._pk_index = None

        # Get schema for validation
        schema_result = db.get_table_schema(table_name)
        if schema_result['success']:
            # Convert schema list to dict keyed by column name
            self._schema = {col['name']: col for col in schema_result['schema']}


# ===========================
# Main Window
# ===========================

class MainWindow(QMainWindow):
    """Main application window with tabbed interface"""

    def __init__(self):
        super().__init__()

        # Initialize managers
        self.db = DatabaseManager()
        self.lang = LanguageManager()
        self.lessons = LessonManager()

        # Ask for language on startup
        self.select_language()

        # Setup UI
        self.init_ui()

    def select_language(self):
        """Show language selection dialog"""
        msg = QMessageBox()
        msg.setWindowTitle("Language / Idioma")
        msg.setText("Select your language / Seleccione su idioma:")

        english_btn = msg.addButton("English", QMessageBox.ButtonRole.AcceptRole)
        spanish_btn = msg.addButton("Español", QMessageBox.ButtonRole.AcceptRole)

        msg.exec()

        if msg.clickedButton() == spanish_btn:
            self.lang.set_language('es')
        else:
            self.lang.set_language('en')

    def init_ui(self):
        """Initialize user interface"""
        self.setWindowTitle(self.lang.get('app_title'))
        self.setGeometry(100, 100, 1200, 800)

        # Create menu bar
        self.create_menu_bar()

        # Create central widget with tabs
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout()
        central_widget.setLayout(layout)

        # Create tab widget
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        # Add tabs
        self.create_beginner_tab()
        self.create_advanced_tab()
        self.create_viewer_tab()
        self.create_console_tab()

        # Connect tab change signal to refresh viewer when switched to
        self.tabs.currentChanged.connect(self.on_tab_changed)

    def create_menu_bar(self):
        """Create application menu bar"""
        menubar = self.menuBar()

        # Language menu
        lang_menu = menubar.addMenu(self.lang.get('language'))

        english_action = QAction('English', self)
        english_action.triggered.connect(lambda: self.change_language('en'))
        lang_menu.addAction(english_action)

        spanish_action = QAction('Español', self)
        spanish_action.triggered.connect(lambda: self.change_language('es'))
        lang_menu.addAction(spanish_action)

        # Database menu
        db_menu = menubar.addMenu(self.lang.get('database'))

        reset_action = QAction(self.lang.get('reset_db'), self)
        reset_action.triggered.connect(self.reset_database)
        db_menu.addAction(reset_action)

        reset_progress_action = QAction(self.lang.get('reset_progress'), self)
        reset_progress_action.triggered.connect(self.reset_lesson_progress)
        db_menu.addAction(reset_progress_action)

    def change_language(self, lang_code):
        """Change application language and refresh UI"""
        self.lang.set_language(lang_code)

        # Show message and require restart for full effect
        msg = QMessageBox()
        msg.setWindowTitle(self.lang.get('language'))
        if lang_code == 'en':
            msg.setText("Language changed to English. Please restart the application for full effect.")
        else:
            msg.setText("Idioma cambiado a Español. Por favor reinicie la aplicación para efecto completo.")
        msg.exec()

    def reset_database(self):
        """Reset database to initial state"""
        reply = QMessageBox.question(
            self,
            self.lang.get('reset_db'),
            self.lang.get('reset_confirm'),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.db.reset_database()
            QMessageBox.information(
                self,
                self.lang.get('reset_db'),
                self.lang.get('reset_success')
            )
            # Refresh table viewer if visible
            if hasattr(self, 'table_viewer'):
                self.refresh_table_viewer()

    def reset_lesson_progress(self):
        """Reset all lesson progress"""
        reply = QMessageBox.question(
            self,
            self.lang.get('reset_progress'),
            self.lang.get('reset_progress_confirm'),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.db.reset_lesson_progress()

            # Refresh beginner lesson combo box to remove checkmarks
            if hasattr(self, 'lesson_combo'):
                current_lesson_id = self.lesson_combo.currentData()
                self.lesson_combo.clear()

                for lesson_id, lesson in self.lessons.beginner_lessons.items():
                    title = lesson['title_es'] if self.lang.current_language == 'es' else lesson['title_en']
                    self.lesson_combo.addItem(title, lesson_id)

                # Restore selection
                index = self.lesson_combo.findData(current_lesson_id)
                if index >= 0:
                    self.lesson_combo.setCurrentIndex(index)

                # Update the current lesson's complete button
                self.display_lesson()

            QMessageBox.information(
                self,
                self.lang.get('reset_progress'),
                self.lang.get('reset_progress_success')
            )

    def create_beginner_tab(self):
        """Create beginner lessons tab"""
        tab = QWidget()
        layout = QVBoxLayout()
        tab.setLayout(layout)

        # Lesson selector
        selector_layout = QHBoxLayout()
        selector_layout.addWidget(QLabel(self.lang.get('select_lesson')))

        self.lesson_combo = QComboBox()
        for lesson_id, lesson in self.lessons.beginner_lessons.items():
            title = lesson['title_es'] if self.lang.current_language == 'es' else lesson['title_en']
            completed = ' ' + self.lang.get('completed') if self.db.is_lesson_complete(lesson_id) else ''
            self.lesson_combo.addItem(title + completed, lesson_id)

        self.lesson_combo.currentIndexChanged.connect(self.display_lesson)
        selector_layout.addWidget(self.lesson_combo)
        selector_layout.addStretch()

        layout.addLayout(selector_layout)

        # Lesson description area
        self.lesson_description = QTextEdit()
        self.lesson_description.setReadOnly(True)
        self.lesson_description.setMaximumHeight(150)
        layout.addWidget(self.lesson_description)

        # SQL code area
        self.lesson_sql = QTextEdit()
        self.lesson_sql.setMaximumHeight(150)
        layout.addWidget(self.lesson_sql)

        # Buttons
        btn_layout = QHBoxLayout()

        self.run_example_btn = QPushButton(self.lang.get('run_example'))
        self.run_example_btn.clicked.connect(self.run_lesson_example)
        btn_layout.addWidget(self.run_example_btn)

        self.mark_complete_btn = QPushButton(self.lang.get('mark_complete'))
        self.mark_complete_btn.clicked.connect(self.mark_lesson_complete)
        btn_layout.addWidget(self.mark_complete_btn)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        # Results area
        self.lesson_results = QTableView()
        self.lesson_model = TableModel()
        self.lesson_results.setModel(self.lesson_model)
        self.lesson_results.setMinimumHeight(200)
        layout.addWidget(self.lesson_results)

        self.tabs.addTab(tab, self.lang.get('tab_beginner'))

        # Display first lesson
        self.display_lesson()

    def display_lesson(self):
        """Display selected lesson content"""
        lesson_id = self.lesson_combo.currentData()
        if not lesson_id:
            return

        lesson = self.lessons.beginner_lessons[lesson_id]

        # Display description
        description = lesson['description_es'] if self.lang.current_language == 'es' else lesson['description_en']
        self.lesson_description.setPlainText(description)

        # Display SQL
        self.lesson_sql.setPlainText(lesson['sql'])

        # Clear results table when switching lessons
        self.lesson_model.update_data([], [])

        # Update complete button
        if self.db.is_lesson_complete(lesson_id):
            self.mark_complete_btn.setText(self.lang.get('completed'))
            self.mark_complete_btn.setEnabled(False)
        else:
            self.mark_complete_btn.setText(self.lang.get('mark_complete'))
            self.mark_complete_btn.setEnabled(True)

    def run_lesson_example(self):
        """Execute the current lesson's SQL example"""
        sql = self.lesson_sql.toPlainText().strip()
        if not sql:
            return

        result = self.db.execute_query(sql)

        if result['success']:
            if 'columns' in result and 'rows' in result:
                self.lesson_model.update_data(result['rows'], result['columns'])
            else:
                QMessageBox.information(self, self.lang.get('success'), result.get('message', ''))
        else:
            QMessageBox.critical(self, self.lang.get('error'), result['error'])

    def mark_lesson_complete(self):
        """Mark current lesson as completed"""
        lesson_id = self.lesson_combo.currentData()
        if lesson_id:
            self.db.mark_lesson_complete(lesson_id)
            self.mark_complete_btn.setText(self.lang.get('completed'))
            self.mark_complete_btn.setEnabled(False)

            # Update combo box text
            current_index = self.lesson_combo.currentIndex()
            current_text = self.lesson_combo.currentText()
            if self.lang.get('completed') not in current_text:
                self.lesson_combo.setItemText(current_index, current_text + ' ' + self.lang.get('completed'))

    def create_advanced_tab(self):
        """Create advanced/dangerous commands tab"""
        tab = QWidget()
        layout = QVBoxLayout()
        tab.setLayout(layout)

        # Warning header
        warning_label = QLabel(self.lang.get('danger_warning'))
        warning_label.setStyleSheet("color: red; font-weight: bold; font-size: 14px;")
        layout.addWidget(warning_label)

        desc_label = QLabel(self.lang.get('danger_desc'))
        layout.addWidget(desc_label)

        # Lesson selector
        selector_layout = QHBoxLayout()
        selector_layout.addWidget(QLabel(self.lang.get('select_lesson')))

        self.adv_lesson_combo = QComboBox()
        for lesson_id, lesson in self.lessons.advanced_lessons.items():
            title = lesson['title_es'] if self.lang.current_language == 'es' else lesson['title_en']
            self.adv_lesson_combo.addItem(title, lesson_id)

        self.adv_lesson_combo.currentIndexChanged.connect(self.display_advanced_lesson)
        selector_layout.addWidget(self.adv_lesson_combo)
        selector_layout.addStretch()

        layout.addLayout(selector_layout)

        # Lesson description
        self.adv_description = QTextEdit()
        self.adv_description.setReadOnly(True)
        self.adv_description.setMaximumHeight(100)
        layout.addWidget(self.adv_description)

        # SQL code area
        self.adv_sql = QTextEdit()
        self.adv_sql.setMaximumHeight(100)
        layout.addWidget(self.adv_sql)

        # Run button
        self.run_adv_btn = QPushButton(self.lang.get('run_example'))
        self.run_adv_btn.clicked.connect(self.run_advanced_example)
        layout.addWidget(self.run_adv_btn)

        # Results area
        self.adv_results = QTextEdit()
        self.adv_results.setReadOnly(True)
        self.adv_results.setMinimumHeight(200)
        layout.addWidget(self.adv_results)

        self.tabs.addTab(tab, self.lang.get('tab_advanced'))

        # Display first lesson
        self.display_advanced_lesson()

    def display_advanced_lesson(self):
        """Display selected advanced lesson"""
        lesson_id = self.adv_lesson_combo.currentData()
        if not lesson_id:
            return

        lesson = self.lessons.advanced_lessons[lesson_id]

        description = lesson['description_es'] if self.lang.current_language == 'es' else lesson['description_en']
        self.adv_description.setPlainText(description)
        self.adv_sql.setPlainText(lesson['sql'])

        # Clear results when switching lessons
        self.adv_results.clear()

    def run_advanced_example(self):
        """Execute advanced/dangerous SQL with confirmation"""
        sql = self.adv_sql.toPlainText().strip()
        if not sql:
            return

        # Confirm execution
        reply = QMessageBox.warning(
            self,
            self.lang.get('danger_warning'),
            self.lang.get('confirm_danger'),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            result = self.db.execute_query(sql)

            if result['success']:
                message = result.get('message', self.lang.get('query_executed'))
                self.adv_results.setPlainText(f"{self.lang.get('success')}: {message}")
            else:
                self.adv_results.setPlainText(f"{self.lang.get('error')}: {result['error']}")

    def create_viewer_tab(self):
        """Create table viewer tab with inline editing support"""
        tab = QWidget()
        layout = QVBoxLayout()
        tab.setLayout(layout)

        # Table selector and action buttons
        selector_layout = QHBoxLayout()
        selector_layout.addWidget(QLabel(self.lang.get('select_table')))

        self.table_combo = QComboBox()
        self.update_table_list()
        self.table_combo.currentIndexChanged.connect(self.refresh_table_viewer)
        selector_layout.addWidget(self.table_combo)

        selector_layout.addStretch()

        # Add Row button
        self.add_row_btn = QPushButton("Add Row")
        self.add_row_btn.clicked.connect(self.add_table_row)
        selector_layout.addWidget(self.add_row_btn)

        # Delete Row button
        self.delete_row_btn = QPushButton("Delete Row")
        self.delete_row_btn.clicked.connect(self.delete_table_row)
        selector_layout.addWidget(self.delete_row_btn)

        layout.addLayout(selector_layout)

        # Table view
        self.table_viewer = QTableView()
        self.viewer_model = TableModel()
        self.table_viewer.setModel(self.viewer_model)

        # Connect SQL signal to display
        self.viewer_model.sql_generated.connect(self.display_sql_command)

        layout.addWidget(self.table_viewer)

        # SQL command display panel
        sql_panel_label = QLabel("Generated SQL Commands:")
        layout.addWidget(sql_panel_label)

        self.sql_display = QTextEdit()
        self.sql_display.setReadOnly(True)
        self.sql_display.setMaximumHeight(100)
        self.sql_display.setPlaceholderText("SQL commands will appear here when you edit, add, or delete rows...")
        layout.addWidget(self.sql_display)

        self.tabs.addTab(tab, self.lang.get('tab_viewer'))

        # Load first table
        if self.table_combo.count() > 0:
            self.refresh_table_viewer()

    def update_table_list(self):
        """Update table dropdown list"""
        self.table_combo.clear()
        tables = self.db.get_table_names()
        self.table_combo.addItems(tables)

    def on_tab_changed(self, index):
        """Handle tab change events - refresh viewer when switched to"""
        # Viewer tab is at index 2 (Beginner=0, Advanced=1, Viewer=2, Console=3)
        if index == 2 and hasattr(self, 'table_combo'):
            # Update table list in case new tables were created
            self.update_table_list()
            # Refresh the currently selected table
            if self.table_combo.count() > 0:
                self.refresh_table_viewer()

    def refresh_table_viewer(self):
        """Refresh table viewer with selected table data and enable editing"""
        table_name = self.table_combo.currentText()
        if not table_name:
            return

        result = self.db.get_table_data(table_name)

        if result['success']:
            # Update data
            self.viewer_model.update_data(result['rows'], result['columns'])

            # Enable editing mode
            self.viewer_model.set_editable(self.db, table_name)

            # Clear SQL display
            self.sql_display.clear()
        else:
            QMessageBox.critical(self, self.lang.get('error'), result['error'])

    def display_sql_command(self, sql):
        """Display generated SQL command in the SQL panel"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        current_text = self.sql_display.toPlainText()

        if current_text:
            new_text = current_text + f"\n[{timestamp}] {sql}"
        else:
            new_text = f"[{timestamp}] {sql}"

        self.sql_display.setPlainText(new_text)

    def add_table_row(self):
        """Add a new row to the current table"""
        table_name = self.table_combo.currentText()
        if not table_name:
            return

        # Get schema to build default row
        schema_result = self.db.get_table_schema(table_name)
        if not schema_result['success']:
            QMessageBox.critical(self, "Error", schema_result['error'])
            return

        schema = schema_result['schema']

        # Create default values for each column
        default_values = []
        for col in schema:
            # Auto-increment primary keys get NULL
            if col['pk'] == 1 and col['type'].upper() == 'INTEGER':
                default_values.append(None)
            elif col['default'] is not None:
                default_values.append(col['default'])
            elif not col['notnull']:
                default_values.append(None)
            elif 'INT' in col['type'].upper():
                default_values.append(0)
            elif 'REAL' in col['type'].upper() or 'FLOAT' in col['type'].upper():
                default_values.append(0.0)
            else:
                default_values.append('')

        # Insert row
        result = self.db.insert_row(table_name, default_values)

        if result['success']:
            # Display SQL
            self.display_sql_command(result['sql'])

            # Refresh table to show new row
            self.refresh_table_viewer()
        else:
            self.display_sql_command(f"ERROR: {result.get('error', 'Unknown error')}")
            QMessageBox.critical(self, "Error", result.get('error', 'Unknown error'))

    def delete_table_row(self):
        """Delete the currently selected row"""
        # Get selected row
        selection = self.table_viewer.selectionModel()
        if not selection.hasSelection():
            QMessageBox.warning(self, "No Selection", "Please select a row to delete")
            return

        indexes = selection.selectedRows()
        if not indexes:
            # Try to get any selected cell
            indexes = selection.selectedIndexes()
            if not indexes:
                QMessageBox.warning(self, "No Selection", "Please select a row to delete")
                return
            # Get the row from the first selected cell
            row_index = indexes[0].row()
        else:
            row_index = indexes[0].row()

        table_name = self.table_combo.currentText()
        if not table_name:
            return

        # Get primary key column and value
        pk_result = self.db.get_primary_key(table_name)
        if not pk_result['success']:
            QMessageBox.critical(self, "Error", pk_result['error'])
            return

        pk_column = pk_result['pk_column']

        # Get PK value from the selected row
        try:
            pk_index = self.viewer_model._columns.index(pk_column)
            pk_value = self.viewer_model._data[row_index][pk_index]
        except (ValueError, IndexError) as e:
            QMessageBox.critical(self, "Error", f"Could not get primary key value: {e}")
            return

        # Confirm deletion
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete the row where {pk_column} = {pk_value}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        # Delete row
        result = self.db.delete_row(table_name, pk_column, pk_value)

        if result['success']:
            # Display SQL
            self.display_sql_command(result['sql'])

            # Refresh table
            self.refresh_table_viewer()
        else:
            self.display_sql_command(f"ERROR: {result.get('error', 'Unknown error')}")
            QMessageBox.critical(self, "Error", result.get('error', 'Unknown error'))

    def create_console_tab(self):
        """Create SQL console tab with query history"""
        tab = QWidget()
        layout = QVBoxLayout()
        tab.setLayout(layout)

        # Title
        layout.addWidget(QLabel(self.lang.get('console_title')))

        # SQL input area
        self.console_input = QTextEdit()
        self.console_input.setPlaceholderText(self.lang.get('query_placeholder'))
        self.console_input.setMaximumHeight(150)
        layout.addWidget(self.console_input)

        # Buttons
        btn_layout = QHBoxLayout()

        execute_btn = QPushButton(self.lang.get('execute_query'))
        execute_btn.clicked.connect(self.execute_console_query)
        btn_layout.addWidget(execute_btn)

        clear_btn = QPushButton(self.lang.get('clear_console'))
        clear_btn.clicked.connect(lambda: self.console_input.clear())
        btn_layout.addWidget(clear_btn)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        # Splitter for results and history
        splitter = QSplitter(Qt.Orientation.Vertical)

        # Results area
        results_widget = QWidget()
        results_layout = QVBoxLayout()
        results_widget.setLayout(results_layout)
        results_layout.addWidget(QLabel("Results:"))

        self.console_results = QTableView()
        self.console_model = TableModel()
        self.console_results.setModel(self.console_model)
        results_layout.addWidget(self.console_results)

        splitter.addWidget(results_widget)

        # History area
        history_widget = QWidget()
        history_layout = QVBoxLayout()
        history_widget.setLayout(history_layout)
        history_layout.addWidget(QLabel(self.lang.get('query_history')))

        self.history_view = QTextEdit()
        self.history_view.setReadOnly(True)
        history_layout.addWidget(self.history_view)

        splitter.addWidget(history_widget)

        layout.addWidget(splitter)

        self.tabs.addTab(tab, self.lang.get('tab_console'))

        # Load query history
        self.update_query_history()

    def execute_console_query(self):
        """Execute query from console"""
        query = self.console_input.toPlainText().strip()
        if not query:
            return

        result = self.db.execute_query(query)

        if result['success']:
            if 'columns' in result and 'rows' in result:
                self.console_model.update_data(result['rows'], result['columns'])
            else:
                QMessageBox.information(self, self.lang.get('success'), result.get('message', ''))
        else:
            QMessageBox.critical(self, self.lang.get('error'), result['error'])

        # Update history
        self.update_query_history()

        # Update table list in case new tables were created
        self.update_table_list()

    def update_query_history(self):
        """Update query history display"""
        history = self.db.get_query_history(20)

        history_text = ""
        for query, timestamp, success, error in history:
            status = self.lang.get('success') if success else self.lang.get('error')
            history_text += f"[{timestamp}] {status}\n"
            history_text += f"{query}\n"
            if error:
                history_text += f"Error: {error}\n"
            history_text += "-" * 50 + "\n"

        self.history_view.setPlainText(history_text)


# ===========================
# Main Entry Point
# ===========================

def main():
    """Application entry point"""
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # Modern look

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == '__main__':
    main()
