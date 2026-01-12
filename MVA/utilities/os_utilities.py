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
        None if directory doesn't exist.
        New directory's path if directory exists. 
    '''
    # Obtain documents path 
    documents_path = Path(user_documents_dir())
    
    # Create new directory's path
    new_directory_path = documents_path / directory_name
    
    # Create new directory id doesn't exist
    if not new_directory_path.exists():
        new_directory_path.mkdir(parents=True)
    else:
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
        raise FileExistsError
