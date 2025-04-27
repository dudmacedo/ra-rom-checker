import argparse
import io
import json
import os
import subprocess
from utils import Systems, bcolors
from shutil import which
from retroachievements import RAClient
from sys import platform


def load_args():
    parser = argparse.ArgumentParser('RetroAchievements ROM Checker')

    parser.add_argument('-u', '--username', default=None, help="API Username")
    parser.add_argument('-k', '--api-key', default=None, help="API Key")
    parser.add_argument('-d', '--dir', help="Roms directory")
    parser.add_argument('-s', '--systemid', type=int, help="ID of target system")
    parser.add_argument('-r', '--remove-invalid', default=False, action="store_true", help="Delete not found roms")
    parser.add_argument('-n', '--rename-files', default=False, action="store_true", help="Automatically correct filenames")
    parser.add_argument('-e', '--dedup-files', default=False, action="store_true", help="Delete duplicated files")

    return parser.parse_args()


def load_session(username: str = None, api_key: str = None) -> None:
    session = None

    if username is None:
        username = input("Your username on RetroAchievements: ")
    
    if api_key is None:
        if os.path.exists(f'{username}.session'):
            with open(f'{username}.session') as session_file:
                session = json.loads(session_file.read())
        else:
            api_key = input("Your web API key: ")
            session = {"username": username, "api_key": api_key}
            with open(f'{username}.session', 'w') as session_file: 
                session_file.write(json.dumps(session))
    else:
        session = {"username": username, "api_key": api_key}
        with open(f'{username}.session', 'w') as session_file: 
            session_file.write(json.dumps(session))
    
    return session


def deduplicate_files(first: str, second: str, system_id: int) -> None:
    hash_first = get_rom_hash(first, system_id)
    hash_second = get_rom_hash(second, system_id)
    if hash_first == hash_second:
        print(f"Delete duplicate {second}")
        os.remove(second)


def get_rom_hash(file: str, system_id: int) -> str:
    process = subprocess.Popen(f'RAHasher {system_id} "{file}"', shell=True, stdout=subprocess.PIPE)
    process.wait()
    for line in io.TextIOWrapper(process.stdout):
        if len(line) > 0:
            return line.strip()


def check_roms(dir: str, auth: RAClient, system_id: int = None, remove_invalid: bool = False, rename_files: bool = False, dedup_files = False) -> None:
    if system_id is None:
        for root, dirs, files in os.walk(dir, topdown=True):
            for name in dirs:
                system = Systems.get_system_by_dir(name)
                if system is not None:
                    check_roms(os.path.join(root, name), auth, system["Id"], remove_invalid, rename_files, dedup_files)
    else:
        system = Systems.get_system_by_id(system_id)
        if system is not None:
            print(f'Checking roms for {system["Name"]}')
        # Load games list from RetroAchievements API
        HASH_DATABASE = {}
        games = auth.get_system_game_list(system_id, hashes=True)
        for g in games:
            for h in g["Hashes"]:
                if h not in HASH_DATABASE.keys():
                    HASH_DATABASE[h] = g

        for root, dirs, files in os.walk(dir, topdown=True):
            for name in files:
                file = os.path.join(root, name)
                game = None

                ra_rom_name = None
                local_rom_name = name.rsplit('.', 1)[0]
                hash = get_rom_hash(file, system_id)
                
                hash_key = None
                if hash.lower() in HASH_DATABASE.keys():
                    hash_key = hash.lower()
                elif hash.upper() in HASH_DATABASE.keys():
                    hash_key = hash.upper()
                
                if hash_key is not None:
                    game = HASH_DATABASE[hash_key]

                    for f in auth.get_game_hashes(game["ID"])["Results"]:
                        if f["MD5"] == hash_key:
                            ra_rom_name = None
                            if system_id in {12, 21, 40}:
                                ra_rom_name = f["Name"]
                            elif system_id == 27:
                                ra_rom_name = f["Name"].split('.', 1)[0]
                            else:
                                ra_rom_name = f["Name"].rsplit('.', 1)[0]
                            
                            if ra_rom_name == local_rom_name:
                                game = f'{bcolors.OKGREEN}{f["Name"]}{bcolors.ENDC}'
                            else:
                                game = f'{bcolors.WARNING}{f["Name"]}{bcolors.ENDC}'
                                    
                
                if game is not None:

                    print(f'{file} - {bcolors.OKGREEN}Hash OK{bcolors.ENDC} - {game}')
                    if rename_files and ra_rom_name is not None and not ra_rom_name == local_rom_name:
                        dest_file = file.replace(local_rom_name, ra_rom_name)
                        if platform == 'win32' and file.lower() == dest_file.lower():
                            os.rename(file, file + '.tmp')
                            file = file + '.tmp'

                        while(True):
                            if not os.path.exists(dest_file):
                                print(f'Renaming to "{ra_rom_name}"...')
                                os.rename(file, dest_file)
                            elif dedup_files:
                                deduplicate_files(file, dest_file, system_id)
                                continue
                            else:
                                print(f'{bcolors.FAIL}Rename fail: Duplicated file name{bcolors.ENDC}')
                            break
                else:
                    print(f'{file} - {bcolors.FAIL}Not found{bcolors.ENDC}')
                    if remove_invalid:
                        print("Deleting...")
                        os.remove(file)


def check_requirements(params):
    print('Checking requirements...')
    error = False

    if which("RAHasher") is None:
        print(f'{bcolors.FAIL}ERROR: "RAHasher" executable must be in PATH{bcolors.ENDC}')
        error = True
    else:
        print(f'{bcolors.OKBLUE}"RAHasher" found{bcolors.ENDC}')

    if error:
        quit()
    else:
        print(f'{bcolors.OKGREEN}[OK]{bcolors.ENDC}')


def main() -> None:
    params = load_args()
    check_requirements(params)

    session = load_session(params.username, params.api_key)
    auth = RAClient(session["username"], session["api_key"])

    check_roms(params.dir, auth, params.systemid, params.remove_invalid, params.rename_files, params.dedup_files)

main()
