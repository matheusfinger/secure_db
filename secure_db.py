import sys
import os
from antlr4 import *
from SimpleSQLLexer import SimpleSQLLexer
from SimpleSQLParser import SimpleSQLParser
from SimpleSQLVisitor import SimpleSQLVisitor
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QTextEdit, QPushButton, QTableWidget, 
                             QTableWidgetItem, QLabel, QMessageBox)
from PyQt5.QtCore import Qt

class SQLQueryVisitor(SimpleSQLVisitor):
    """Visitor para executar consultas SQL"""
    
    def __init__(self, data_file):
        self.data_file = data_file
        self.columns = ['nome', 'cpf', 'matricula', 'sexo', 'salario', 'idade']
        self.data = self.load_data()
        
    def load_data(self):
        """Carrega dados do arquivo"""
        data = []
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        fields = line.strip().split(';')
                        if len(fields) == 6:
                            # Converte tipos
                            fields[4] = float(fields[4])  # salario
                            fields[5] = int(fields[5])    # idade
                            data.append(dict(zip(self.columns, fields)))
            return data
        except FileNotFoundError:
            raise Exception(f"Arquivo {self.data_file} não encontrado")
    
    def visitSelect_statement(self, ctx:SimpleSQLParser.Select_statementContext):
        """Processa SELECT statement"""
        # Obtém colunas selecionadas
        select_cols_ctx = ctx.select_columns()
        
        if select_cols_ctx.getText() == '*':
            selected_columns = self.columns
        else:
            selected_columns = []
            for col in select_cols_ctx.column_list().column_name():
                col_name = col.getText().lower()
                if col_name not in self.columns:
                    raise Exception(f"Coluna '{col_name}' não existe. Colunas disponíveis: {', '.join(self.columns)}")
                selected_columns.append(col_name)
        
        # Filtra dados com WHERE se existir
        filtered_data = self.data
        if ctx.where_condition():
            filtered_data = self.visitWhere_condition(ctx.where_condition())
        
        # Seleciona colunas
        result_data = []
        for row in filtered_data:
            result_row = [row[col] for col in selected_columns]
            result_data.append(result_row)
        
        return selected_columns, result_data
    
    def visitWhere_condition(self, ctx:SimpleSQLParser.Where_conditionContext):
        """Processa WHERE condition"""
        return self.visitExpression(ctx.expression())
    
    def visitExpression(self, ctx:SimpleSQLParser.ExpressionContext):
        """Processa expressão WHERE"""
        column_name = ctx.column_name().getText().lower()
        operator = ctx.comparison_operator().getText()
        value_ctx = ctx.value()
        
        # Verifica se a coluna existe
        if column_name not in self.columns:
            raise Exception(f"Coluna '{column_name}' não existe na cláusula WHERE")
        
        # Obtém o valor
        if value_ctx.STRING():
            value = value_ctx.getText()[1:-1]  # Remove aspas
        else:  # NUMBER
            value_text = value_ctx.getText()
            if '.' in value_text:
                value = float(value_text)
            else:
                value = int(value_text)
        
        # Filtra os dados
        filtered_data = []
        for row in self.data:
            row_value = row[column_name]
            
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
                # Se houver erro de tipo na comparação, ignora esta linha
                continue
        
        return filtered_data

class SecureDB(QMainWindow):
    def __init__(self):
        super().__init__()
        self.sql_visitor = None
        self.init_ui()
        
    def init_ui(self):
        """Inicializa a interface do usuário"""
        self.setWindowTitle('Secure DB')
        self.setGeometry(100, 100, 1200, 700)
        
        # Aplica estilo moderno
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
        
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal
        main_layout = QVBoxLayout()
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 20, 20)
        central_widget.setLayout(main_layout)
        
        # Título
        title_label = QLabel('🔒 Secure DB')
        title_label.setObjectName('title')
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)
        
        # Área de consulta
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
            '  SELECT * FROM empregado WHERE sexo = \'F\' AND salario > 5000'
        )
        main_layout.addWidget(self.sql_input)
        
        # Botão executar
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
        
        # Grid de resultados
        results_label = QLabel('Resultados da Consulta')
        results_label.setStyleSheet('color: #ffffff; font-size: 14px; font-weight: bold; margin-top: 20px;')
        main_layout.addWidget(results_label)
        
        self.result_table = QTableWidget()
        self.result_table.setAlternatingRowColors(True)
        self.result_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.result_table.setEditTriggers(QTableWidget.NoEditTriggers)
        main_layout.addWidget(self.result_table)
        
        # Status bar
        self.status_label = QLabel('✅ Pronto para consultas')
        self.status_label.setObjectName('status')
        main_layout.addWidget(self.status_label)
        
        # Carrega os dados
        self.load_database()
    
    def load_database(self):
        """Carrega o banco de dados"""
        try:
            self.sql_visitor = SQLQueryVisitor('empregados.txt')
            self.status_label.setText(f'✅ Banco de dados carregado - {len(self.sql_visitor.data)} registros disponíveis')
            self.status_label.setObjectName('status')
            self.status_label.setStyleSheet('')
        except Exception as e:
            self.status_label.setText(f'❌ Erro ao carregar banco de dados: {str(e)}')
            self.status_label.setObjectName('error')
    
    def execute_query(self):
        """Executa a consulta SQL"""
        if not self.sql_visitor:
            QMessageBox.warning(self, 'Aviso', 'Banco de dados não carregado!')
            return
        
        query = self.sql_input.toPlainText().strip()
        
        if not query:
            QMessageBox.warning(self, 'Aviso', 'Por favor, digite uma consulta SQL')
            return
        
        # Verifica se é apenas SELECT
        if not query.lower().strip().startswith('select'):
            QMessageBox.warning(self, 'Consulta Inválida', 'Apenas consultas SELECT são permitidas neste sistema!')
            return
        
        try:
            # Parsing da consulta
            input_stream = InputStream(query)
            lexer = SimpleSQLLexer(input_stream)
            stream = CommonTokenStream(lexer)
            parser = SimpleSQLParser(stream)
            tree = parser.parse()
            
            # Executa a consulta
            columns, data = self.sql_visitor.visit(tree)
            
            # Exibe resultados
            self.display_results(columns, data)
            
            # Atualiza status
            self.status_label.setText(f'✅ Consulta executada com sucesso - {len(data)} registro(s) encontrado(s)')
            self.status_label.setObjectName('status')
            
        except Exception as e:
            self.status_label.setText(f'❌ Erro na consulta: {str(e)}')
            self.status_label.setObjectName('error')
            QMessageBox.critical(self, 'Erro na Consulta', f'Erro ao executar consulta:\n\n{str(e)}')
    
    def display_results(self, columns, data):
        """Exibe os resultados na tabela"""
        self.result_table.clear()
        
        if not data:
            self.result_table.setRowCount(0)
            self.result_table.setColumnCount(len(columns))
            self.result_table.setHorizontalHeaderLabels([col.upper() for col in columns])
            return
        
        self.result_table.setRowCount(len(data))
        self.result_table.setColumnCount(len(columns))
        
        # Configura cabeçalhos
        self.result_table.setHorizontalHeaderLabels([col.upper() for col in columns])
        
        # Preenche dados
        for i, row in enumerate(data):
            for j, value in enumerate(row):
                # Formata valores
                if isinstance(value, float):
                    display_value = f'R$ {value:,.2f}'
                elif isinstance(value, int):
                    display_value = str(value)
                else:
                    display_value = str(value)
                
                item = QTableWidgetItem(display_value)
                item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                
                # Alinha números à direita
                if isinstance(value, (int, float)):
                    item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                
                self.result_table.setItem(i, j, item)
        
        # Ajusta tamanho das colunas
        self.result_table.resizeColumnsToContents()
        
        # Ajusta altura das linhas
        self.result_table.resizeRowsToContents()
    
    def clear_query(self):
        """Limpa a consulta e os resultados"""
        self.sql_input.clear()
        self.result_table.clear()
        self.result_table.setRowCount(0)
        self.result_table.setColumnCount(0)
        self.status_label.setText('✅ Pronto para consultas')
        self.status_label.setObjectName('status')

def create_sample_file():
    """Cria um arquivo de exemplo se não existir"""
    sample_data = [
        "Beatriz Costa;869.692.983-70;341733;F;8374.65;30",
        "Pedro Santos;344.262.312-05;413147;M;13743.62;27",
        "Carlos Silva;918.680.284-45;338638;M;8293.63;43",
        "Rodrigo Barbosa;500.993.034-00;552363;M;6554.53;53",
        "Débora Nascimento;990.930.821-59;732426;F;6312.33;39",
        "Luciana Mendes;268.556.192-74;920759;F;4341.44;45",
        "Ana Paula Souza;123.456.789-00;123456;F;9876.54;28",
        "João Oliveira;987.654.321-00;654321;M;11234.56;35",
        "Mariana Santos;456.789.123-00;789123;F;5432.10;31",
        "Ricardo Alves;111.222.333-44;456789;M;15234.89;38",
        "Fernanda Lima;555.666.777-88;987654;F;9234.67;29",
        "Roberto Mendes;999.888.777-66;321654;M;7345.12;42"
    ]
    
    try:
        with open('empregados.txt', 'w', encoding='utf-8') as file:
            for line in sample_data:
                file.write(line + '\n')
        print("✅ Arquivo empregados.txt criado com sucesso!")
    except Exception as e:
        print(f"❌ Erro ao criar arquivo: {e}")

def main():
    # Cria arquivo de exemplo se não existir
    if not os.path.exists('empregados.txt'):
        create_sample_file()
    
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    window = SecureDB()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()