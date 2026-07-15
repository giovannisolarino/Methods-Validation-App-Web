import os
from platformdirs import user_documents_dir
from pathlib import Path
from nicegui import app

def clear():
    """Clear all relevant user session data in a server-safe way."""
    app.storage.user.clear()

def create_documents_directory(directory_name = 'MVAStorage'):
    '''
    Obtain documents path for OS used and create new directory
    if doesn't exist.

    Params:
        directory_name: string containing new directory's name, default 'MVAStorage'
    
    Returns:
        The directory's path, creating it first if it doesn't exist.
    '''
    documents_path = Path(user_documents_dir())
    new_directory_path = documents_path / directory_name
    new_directory_path.mkdir(parents=True, exist_ok=True)
    return new_directory_path

    

def load_files_from_folder():
    '''
    Obtain files' list contained in a specific folder.

    Returns:
        Files' list
    '''
    path = create_documents_directory()

    if os.path.exists(path):
        file_list = os.listdir(path)
        return file_list, path
    else:
        raise FileNotFoundError(f'Storage directory not found: {path}')
