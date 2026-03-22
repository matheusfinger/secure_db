import sys
import re
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QTextEdit, QPushButton, QTableWidget, 
                             QTableWidgetItem, QLabel, QMessageBox)
from PyQt5.QtCore import Qt

# Constantes
DATA_FILE = 'empregados.txt'
COLUMNS = ['nome', 'cpf', 'matricula', 'sexo', 'salario', 'idade']

# Tokens
class Token:
    def __init__(self, type_, value, line, column):
        self.type = type_
        self.value = value
        self.line = line
        self.column = column
    
    def __repr__(self):
        return f"Token({self.type}, {self.value})"

class Lexer:
    """Lexer manual para a gramática SQL simplificada"""
    
    def __init__(self, text):
        self.text = text
        self.pos = 0
        self.line = 1
        self.column = 1
        self.tokens = []
        
    def tokenize(self):
        """Converte o texto em uma lista de tokens"""
        while self.pos < len(self.text):
            char = self.text[self.pos]
            
            # Pular whitespace
            if char in ' \t\r\n':
                if char == '\n':
                    self.line += 1
                    self.column = 1
                else:
                    self.column += 1
                self.pos += 1
                continue
            
            # Palavras-chave e identificadores
            if char.isalpha() or char == '_':
                self._read_identifier()
                continue
            
            # Strings
            if char == "'":
                self._read_string()
                continue
            
            # Números
            if char.isdigit():
                self._read_number()
                continue
            
            # Operadores e outros símbolos
            if char in '=<>!':
                self._read_operator()
                continue
            
            if char == '*':
                self.tokens.append(Token('STAR', '*', self.line, self.column))
                self.pos += 1
                self.column += 1
                continue
            
            if char == ',':
                self.tokens.append(Token('COMMA', ',', self.line, self.column))
                self.pos += 1
                self.column += 1
                continue
            
            raise Exception(f"Caractere inválido '{char}' na linha {self.line}, coluna {self.column}")
        
        self.tokens.append(Token('EOF', None, self.line, self.column))
        return self.tokens
    
    def _read_identifier(self):
        """Lê um identificador ou palavra-chave"""
        start = self.pos
        start_column = self.column
        
        while self.pos < len(self.text) and (self.text[self.pos].isalnum() or self.text[self.pos] == '_'):
            self.pos += 1
            self.column += 1
        
        value = self.text[start:self.pos]
        value_upper = value.upper()
        
        # Verifica se é palavra-chave
        if value_upper == 'SELECT':
            self.tokens.append(Token('SELECT', value, self.line, start_column))
        elif value_upper == 'FROM':
            self.tokens.append(Token('FROM', value, self.line, start_column))
        elif value_upper == 'WHERE':
            self.tokens.append(Token('WHERE', value, self.line, start_column))
        else:
            self.tokens.append(Token('IDENTIFIER', value, self.line, start_column))
    
    def _read_string(self):
        """Lê uma string entre aspas simples"""
        start = self.pos
        start_column = self.column
        self.pos += 1  # Pula a aspa inicial
        self.column += 1
        
        while self.pos < len(self.text) and self.text[self.pos] != "'":
            if self.text[self.pos] == '\n':
                self.line += 1
                self.column = 1
            else:
                self.column += 1
            self.pos += 1
        
        if self.pos >= len(self.text):
            raise Exception(f"String não fechada na linha {self.line}")
        
        self.pos += 1  # Pula a aspa final
        self.column += 1
        value = self.text[start:self.pos]
        self.tokens.append(Token('STRING', value, self.line, start_column))
    
    def _read_number(self):
        """Lê um número"""
        start = self.pos
        start_column = self.column
        has_dot = False
        
        while self.pos < len(self.text) and (self.text[self.pos].isdigit() or self.text[self.pos] == '.'):
            if self.text[self.pos] == '.':
                if has_dot:
                    break
                has_dot = True
            self.pos += 1
            self.column += 1
        
        value = self.text[start:self.pos]
        self.tokens.append(Token('NUMBER', value, self.line, start_column))
    
    def _read_operator(self):
        """Lê um operador de comparação"""
        start = self.pos
        start_column = self.column
        char = self.text[self.pos]
        
        if self.pos + 1 < len(self.text) and self.text[self.pos + 1] == '=':
            operator = char + '='
            self.pos += 2
            self.column += 2
        else:
            operator = char
            self.pos += 1
            self.column += 1
        
        if operator in ['=', '>', '<', '>=', '<=', '!=']:
            self.tokens.append(Token('OPERATOR', operator, self.line, start_column))
        else:
            raise Exception(f"Operador inválido '{operator}' na linha {self.line}")

class Parser:
    """Parser manual para a gramática SQL simplificada"""
    
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0
    
    def parse(self):
        """Parseia a entrada completa"""
        result = self.parse_select_statement()
        self._match('EOF')
        return result
    
    def parse_select_statement(self):
        """Parseia SELECT statement"""
        self._match('SELECT')
        columns = self.parse_select_columns()
        self._match('FROM')
        table = self._match('IDENTIFIER')

        if table.value.lower() != 'empregados' and table.value.lower() != 'empregado':
            raise Exception(table.value.lower())
        
        where_condition = None
        if self._peek() == 'WHERE':
            self._match('WHERE')
            where_condition = self.parse_where_condition()
        
        return {
            'type': 'SELECT',
            'columns': columns,
            'table': table.value,
            'where': where_condition
        }
    
    def parse_select_columns(self):
        """Parseia lista de colunas"""
        if self._peek() == 'STAR':
            self._match('STAR')
            return '*'
        else:
            return self.parse_column_list()
    
    def parse_column_list(self):
        """Parseia lista de colunas separadas por vírgula"""
        columns = [self._match('IDENTIFIER').value]
        
        while self._peek() == 'COMMA':
            self._match('COMMA')
            columns.append(self._match('IDENTIFIER').value)
        
        return columns
    
    def parse_where_condition(self):
        """Parseia condição WHERE"""
        return self.parse_expression()
    
    def parse_expression(self):
        """Parseia expressão"""
        column = self._match('IDENTIFIER').value
        operator = self._match('OPERATOR').value
        value_token = self._match(['STRING', 'NUMBER'])
        value = value_token.value
        
        # Remove aspas das strings
        if value_token.type == 'STRING':
            value = value[1:-1]
        else:
            # Converte número
            if '.' in value:
                value = float(value)
            else:
                value = int(value)
        
        return {
            'column': column,
            'operator': operator,
            'value': value
        }
    
    def _match(self, expected):
        """Verifica e consome um token esperado"""
        if isinstance(expected, list):
            if self.pos >= len(self.tokens):
                raise Exception(f"Fim de arquivo inesperado, esperava {expected}")
            token = self.tokens[self.pos]
            if token.type not in expected:
                raise Exception(f"Esperava {expected}, encontrou {token.type} '{token.value}' na linha {token.line}")
            self.pos += 1
            return token
        else:
            if self.pos >= len(self.tokens):
                raise Exception(f"Fim de arquivo inesperado, esperava {expected}")
            token = self.tokens[self.pos]
            if token.type != expected:
                raise Exception(f"Esperava {expected}, encontrou {token.type} '{token.value}' na linha {token.line}")
            self.pos += 1
            return token
    
    def _peek(self):
        """Olha o próximo token sem consumir"""
        if self.pos < len(self.tokens):
            return self.tokens[self.pos].type
        return 'EOF'

def load_data():
    """Carrega dados do arquivo"""
    data = []
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    fields = line.strip().split(';')
                    if len(fields) == 6:
                        fields[4] = float(fields[4])
                        fields[5] = int(fields[5])
                        data.append(dict(zip(COLUMNS, fields)))
        return data
    except FileNotFoundError:
        raise Exception(f"Arquivo {DATA_FILE} não encontrado")

def execute_query(parsed_query, data):
    """Executa a consulta parseada"""
    # Verifica se é SELECT
    if parsed_query['type'] != 'SELECT':
        raise Exception("Apenas consultas SELECT são suportadas")
    
    # Seleciona colunas
    if parsed_query['columns'] == '*':
        selected_columns = COLUMNS
    else:
        selected_columns = []
        for col in parsed_query['columns']:
            if col.lower() not in COLUMNS:
                raise Exception(f"Coluna '{col}' não existe. Colunas disponíveis: {', '.join(COLUMNS)}")
            selected_columns.append(col.lower())
    
    # Aplica filtro WHERE
    filtered_data = data
    if parsed_query['where']:
        where = parsed_query['where']
        filtered_data = []
        
        for row in data:
            row_value = row[where['column'].lower()]
            value = where['value']
            operator = where['operator']
            
            try:
                if operator == '=':
                    if str(row_value).lower() == str(value).lower() if isinstance(row_value, str) else row_value == value:
                        filtered_data.append(row)
                elif operator == '>':
                    if row_value > value:
                        filtered_data.append(row)
                elif operator == '<':
                    if row_value < value:
                        filtered_data.append(row)
                elif operator == '>=':
                    if row_value >= value:
                        filtered_data.append(row)
                elif operator == '<=':
                    if row_value <= value:
                        filtered_data.append(row)
                elif operator == '!=':
                    if str(row_value).lower() != str(value).lower() if isinstance(row_value, str) else row_value != value:
                        filtered_data.append(row)
            except TypeError:
                continue
    
    # Prepara resultados
    result_data = []
    for row in filtered_data:
        result_row = [row[col] for col in selected_columns]
        result_data.append(result_row)
    
    return selected_columns, result_data

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.data = None
        self.init_ui()
        
    def init_ui(self):
        """Inicializa a interface do usuário"""
        self.setWindowTitle('Secure DB - Consulta SQL')
        self.setGeometry(100, 100, 1200, 700)
        
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e1e2e;
            }
            QLabel#title {
                color: #4CAF50;
                font-size: 32px;
                font-weight: bold;
                padding: 20px;
                background-color: #2d2d3a;
                border-radius: 10px;
            }
            QTextEdit {
                background-color: #2d2d3a;
                color: #ffffff;
                font-family: 'Courier New', monospace;
                font-size: 14px;
                border: 2px solid #4CAF50;
                border-radius: 8px;
                padding: 10px;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 8px;
                font-size: 14px;
                font-weight: bold;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
            QTableWidget {
                background-color: #2d2d3a;
                color: #ffffff;
                border: 1px solid #4CAF50;
                border-radius: 8px;
                gridline-color: #3d3d4a;
                alternate-background-color: #353545;
            }
            QTableWidget::item {
                padding: 8px;
            }
            QHeaderView::section {
                background-color: #4CAF50;
                color: white;
                padding: 8px;
                border: none;
                font-weight: bold;
            }
            QLabel#status {
                color: #4CAF50;
                padding: 10px;
                font-size: 12px;
                background-color: #2d2d3a;
                border-radius: 5px;
            }
            QLabel#error {
                color: #ff6b6b;
                padding: 10px;
                font-size: 12px;
                background-color: #2d2d3a;
                border-radius: 5px;
            }
        """)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout()
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 20, 20)
        central_widget.setLayout(main_layout)
        
        title_label = QLabel('🔒 Secure DB - Consulta SQL')
        title_label.setObjectName('title')
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)
        
        query_label = QLabel('Consulta SQL (somente leitura)')
        query_label.setStyleSheet('color: #ffffff; font-size: 14px; font-weight: bold; margin-top: 10px;')
        main_layout.addWidget(query_label)
        
        self.sql_input = QTextEdit()
        self.sql_input.setMaximumHeight(150)
        self.sql_input.setPlaceholderText(
            'Digite sua consulta SELECT aqui...\n\n'
            'Exemplos:\n'
            '  SELECT * FROM empregado\n'
            '  SELECT nome, salario FROM empregado WHERE idade > 30\n'
            '  SELECT * FROM empregado WHERE sexo = \'F\''
        )
        main_layout.addWidget(self.sql_input)
        
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.execute_btn = QPushButton('🔍 Executar Consulta')
        self.execute_btn.clicked.connect(self.execute_query)
        button_layout.addWidget(self.execute_btn)
        
        self.clear_btn = QPushButton('🗑 Limpar')
        self.clear_btn.clicked.connect(self.clear_query)
        button_layout.addWidget(self.clear_btn)
        
        button_layout.addStretch()
        main_layout.addLayout(button_layout)
        
        results_label = QLabel('Resultados da Consulta')
        results_label.setStyleSheet('color: #ffffff; font-size: 14px; font-weight: bold; margin-top: 20px;')
        main_layout.addWidget(results_label)
        
        self.result_table = QTableWidget()
        self.result_table.setAlternatingRowColors(True)
        self.result_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.result_table.setEditTriggers(QTableWidget.NoEditTriggers)
        main_layout.addWidget(self.result_table)
        
        self.status_label = QLabel('✅ Pronto para consultas')
        self.status_label.setObjectName('status')
        main_layout.addWidget(self.status_label)
        
        self.load_database()
    
    def load_database(self):
        """Carrega o banco de dados"""
        try:
            self.data = load_data()
            self.status_label.setText(f'✅ Banco de dados carregado - {len(self.data)} registros disponíveis')
            self.status_label.setObjectName('status')
        except Exception as e:
            self.status_label.setText(f'❌ Erro ao carregar banco de dados: {str(e)}')
            self.status_label.setObjectName('error')
    
    def execute_query(self):
        """Executa a consulta SQL"""
        if not self.data:
            QMessageBox.warning(self, 'Aviso', 'Banco de dados não carregado!')
            return
        
        query = self.sql_input.toPlainText().strip()
        
        if not query:
            QMessageBox.warning(self, 'Aviso', 'Por favor, digite uma consulta SQL')
            return
        
        try:
            # Tokeniza e parseia
            lexer = Lexer(query)
            tokens = lexer.tokenize()
            parser = Parser(tokens)
            parsed_query = parser.parse()
            
            # Executa
            columns, data = execute_query(parsed_query, self.data)
            
            # Exibe resultados
            self.display_results(columns, data)
            
            self.status_label.setText(f'✅ Consulta executada com sucesso - {len(data)} registro(s) encontrado(s)')
            self.status_label.setObjectName('status')
            
        except Exception as e:
            self.status_label.setText(f'❌ Erro na consulta: {str(e)}')
            self.status_label.setObjectName('error')
            QMessageBox.critical(self, 'Erro na Consulta', f'Erro ao executar consulta:\n\n{str(e)}')
    
    def display_results(self, columns, data):
        """Exibe os resultados na tabela"""
        self.result_table.clear()
        
        self.result_table.setRowCount(len(data))
        self.result_table.setColumnCount(len(columns))
        self.result_table.setHorizontalHeaderLabels([col.upper() for col in columns])
        
        for i, row in enumerate(data):
            for j, value in enumerate(row):
                if isinstance(value, float):
                    display_value = f'R$ {value:,.2f}'
                elif isinstance(value, int):
                    display_value = str(value)
                else:
                    display_value = str(value)
                
                item = QTableWidgetItem(display_value)
                
                if isinstance(value, (int, float)):
                    item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                else:
                    item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                
                self.result_table.setItem(i, j, item)
        
        self.result_table.resizeColumnsToContents()
        self.result_table.resizeRowsToContents()
    
    def clear_query(self):
        """Limpa a consulta e os resultados"""
        self.sql_input.clear()
        self.result_table.clear()
        self.result_table.setRowCount(0)
        self.result_table.setColumnCount(0)
        self.status_label.setText('✅ Pronto para consultas')
        self.status_label.setObjectName('status')

def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()