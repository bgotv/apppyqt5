import os
import shutil
import sys

def flatten_convert(src_root: str, dst_root: str):
    """
    Copia todos os arquivos de src_root para dst_root (uma única pasta),
    substituindo .py por .txt e incluindo a estrutura de pastas no nome.
    """
    if not os.path.isdir(src_root):
        print(f"Erro: pasta de origem não existe: {src_root}")
        sys.exit(1)

    os.makedirs(dst_root, exist_ok=True)

    for dirpath, _, filenames in os.walk(src_root):
        for filename in filenames:
            src_file = os.path.join(dirpath, filename)
            # caminho relativo desde a raiz do projeto
            rel_path = os.path.relpath(src_file, src_root)
            rel_root, ext = os.path.splitext(rel_path)
            ext_lower = ext.lower()

            # define extensão de saída
            if ext_lower == '.py':
                new_ext = '.txt'
            else:
                new_ext = ext

            # monta nome seguro: substitui separadores de pasta por "__"
            safe_name = rel_root.replace(os.sep, '__') + new_ext
            dst_file = os.path.join(dst_root, safe_name)

            shutil.copy2(src_file, dst_file)

    print(f"[OK] Todos os arquivos de '{src_root}' foram copiados para '{dst_root}'.")

if __name__ == "__main__":
    print("=== FLATTEN & .py → .txt ===")
    origem = 'C:\\Users\\2006428\\PycharmProjects\\pythonProject\\Projetos\\Scripts\\GD\\Estruturado\\Analise_GD_ModV2_Fernando\\app_pyqt5'
    destino = 'C:\\Users\\2006428\\PycharmProjects\\pythonProject\\Projetos\\Scripts\\GD\\Estruturado\\Analise_GD_ModV2_Fernando\\app_pyqt5_txt'
    flatten_convert(origem, destino)
