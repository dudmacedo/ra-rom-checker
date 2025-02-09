import json


class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

class Systems(object):
    SYSTEMS_BY_ID = None
    SYSTEMS_BY_DIR = None

    @staticmethod
    def load_systems() -> dict:
        with open('systems.json') as systems_file:
            systems = json.loads(systems_file.read())
            Systems.SYSTEMS_BY_ID = {}
            Systems.SYSTEMS_BY_DIR = {}
            for s in systems["Systems"]:
                Systems.SYSTEMS_BY_ID[s["Id"]] = s
                for d in s["Dir"]:
                    Systems.SYSTEMS_BY_DIR[d] = s


    @staticmethod
    def get_system_by_id(id: int) -> dict:
        if Systems.SYSTEMS_BY_ID == None:
            Systems.load_systems()
        return Systems.SYSTEMS_BY_ID[id] if id in Systems.SYSTEMS_BY_ID.keys() else None

    @staticmethod
    def get_system_by_dir(dir: str) -> dict:
        if Systems.SYSTEMS_BY_DIR is None:
            Systems.load_systems()
        return Systems.SYSTEMS_BY_DIR[dir] if dir in Systems.SYSTEMS_BY_DIR.keys() else None
