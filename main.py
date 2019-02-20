import sys

from src.providers.dropbox import Dropbox
#from src.providers.onedrive import OneDrive
from fuse import FUSE, FuseOSError
from src.fuse.fuse_test import Passthrough

def ler_ficheiro(path):
    """Esta função recebe um caminho para o ficheiro (path) e devolve o array de bytes lidos.

    Args:
        path (string): O caminho absoluto para o ficheiro, por exemplo, `/home/student/Desktop/playground`.

    Returns
        bytes: O conjunto de bytes que escritos no ficheiro

    Raises:
        FileNotFoundError: Se o ficheiro não existir vai lançar este error
    """

    # Ler os bytes do ficheiro
    with open(path, 'rb') as file:
        data = file.read()
        file.close()

    # Devolver o array de bytes lido
    return data

def escrever_ficheiro(path, data):
    """Esta escreve um conjunto de dados para um ficheiro localmente.

    Args:
        path (stribg): O caminho na máquina onde os dados vão ser guardados, por exemplo, `/home/student/Desktop/playground`
        provider (Dropbox|OneDrive): A instância da classe correspondente ao provedor, Dropbox ou One Drive.
    """

    # Abrir o ficheiro para escrita
    with open(path, 'wb') as file:
        file.write(data)
        file.close()


def upload_dados(data, path, provider):
    """Esta função recebe um byte array, um caminho onde o ficheiro deve ser guardado e o provedor cloud.

    Args:
        data (bytes): O conjunto de bytes que é pretendido enviar para a provedor
        path (string): O caminho na provedor onde os dados devem ser guardados, por exemplo, `project/cloud/program.txt`
        provider (Dropbox|OneDrive): A instância da classe correspondente ao provedor, Dropbox ou One Drive.
    """

    provider.put(data, path)



def download_dados(path, provider):
    """Esta função recebe um caminho onde o ficheiro está guardado e provedor cloud.

    Args:
        path (string): O caminho na provedor onde os dados estão guardados, por exemplo, `project/cloud/program.txt`
        provider (Dropbox|OneDrive): A instância da classe correspondente ao provedor, Dropbox ou One Drive.

    Returns:
        [ bytes ]: Um array de bytearrays com os dados e com o tamanho igual ao número de provedores configurados.
    """

    return provider.get(path)

def main(mountpoint, root):
    # Número de provedores
    providers_number = 1

    # Providor Dropbox
    dropbox = Dropbox()

    # Providor OneDrive
    #one_drive = OneDrive()

    # Fuse Implementation
    fuseImpl = Passthrough(root)

    # Ler ficheiro
    data = ler_ficheiro('informatica')
    print('Ficheiro lido com sucesso, conteúdo: ' + str(data))
    print('\n')

    # Enviar para os provedores
    upload_dados(data , '/informatica', dropbox)
    print('Ficheiro enviado para o dropbox com sucesso')
    print('\n')

    # Ler dos provedores
    dropbox_data = download_dados('/informatica', dropbox)
    print('Ficheiro lido do one drive com sucesso, conteúdo: ' + str(dropbox_data))
    print('\n')

    FUSE(fuseImpl, mountpoint, nothreads=True, foreground=True)

if __name__ == '__main__':
    main(sys.argv[2], sys.argv[1])