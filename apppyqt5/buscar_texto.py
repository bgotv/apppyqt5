import os
import re

def search_text_in_modules(directory, text):
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(root, file)
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if re.search(text, content):
                        print(f"Texto encontrado em: {file_path}")

# Exemplo de uso
search_text_in_modules(r'C:\Users\2006428\PycharmProjects\pythonProject\Projetos\Scripts\GD\Estruturado\Analise_GD_ModV2_Fernando\app_pyqt5', 'Atualizar Métricas')
# search_text_in_modules(r'C:\Users\2006428\PycharmProjects\pythonProject\Projetos\Scripts\Tramitação', '7120/btnDETAL')
