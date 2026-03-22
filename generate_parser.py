import subprocess
import sys

def generate_parser():
    """Gera os arquivos do parser ANTLR"""
    
    print("Gerando parser ANTLR")
    
    cmd = [
        'java', '-jar', 'antlr-4.13.1-complete.jar',
        '-Dlanguage=Python3',
        '-visitor',
        'SimpleSQL.g4'
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print("Parser gerado com sucesso")
            return True
        else:
            print(f"Erro ao gerar parser: {result.stderr}")
            return False
    except FileNotFoundError:
        print("Java não encontrado ou ANTLR JAR não está na pasta!")
        return False

if __name__ == '__main__':
    generate_parser()