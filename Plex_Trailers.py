#!/usr/bin/python
"""Update Plex preroll trailers based on the current month."""

import logging

try:
    from plexapi.server import PlexServer
except ImportError as exc:
    raise ImportError(
        "PlexAPI is required. Install dependencies with 'pip install -r requirements.txt'."
    ) from exc

import requests
from datetime import datetime

from argparse import ArgumentParser
import os
import pathlib
from configparser import ConfigParser


def configure_logging(level_name="INFO", log_file=None):
    level = getattr(logging, level_name.upper(), logging.INFO)
    logging.basicConfig(
        level=level,
        filename=log_file,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )


def show_banner():
    logging.info("###########################")
    logging.info("#                         #")
    logging.info("#  Plex Monthly Preroll!  #")
    logging.info("#                         #")
    logging.info("###########################" + "\n")
    logging.info("Pre-roll updating...")

def getArguments():
    name = 'Monthly-Plex-Preroll-Trailers'
    version = '1.0.1'
    parser = ArgumentParser(description='{}: Set monthly trailers for Plex'.format(name))
    parser.add_argument("-v", "--version", action='version', version='{} {}'.format(name, version), help="show the version number and exit")
    parser.add_argument("--log-level", default="INFO", help="Set log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)")
    parser.add_argument("--log-file", help="Path to log file")
    return parser.parse_args()

def getConfig():
    config_path = pathlib.Path("config.ini")
    if not config_path.exists():
        logging.info('No config file found! Lets set one up!')
        file1 = open("config.ini","w+")
        file1.write("[SERVER]\n")
        x = input("Enter your (https) plex url:")
        file1.write("plex_url = " + x + "\n")
        x = input("Enter your plex token: (not sure what that is go here: https://support.plex.tv/articles/204059436-finding-an-authentication-token-x-plex-token/)")
        file1.write("plex_token = " + x + "\n\n")
        file1.write("[MONTHS]\n")
        logging.info('Make sure plex can access the path you enter!')
        x = input("Enter the January trailer path:")
        file1.write("Jan = " + x + "\n")
        x = input("Enter the February trailer path:")
        file1.write("Feb = " + x + "\n")
        x = input("Enter the March trailer path:")
        file1.write("Mar = " + x + "\n")
        x = input("Enter the April trailer path:")
        file1.write("Apr = " + x + "\n")
        x = input("Enter the May trailer path:")
        file1.write("May = " + x + "\n")
        x = input("Enter the June trailer path:")
        file1.write("Jun = " + x + "\n")
        x = input("Enter the July trailer path:")
        file1.write("Jul = " + x + "\n")
        x = input("Enter the August trailer path:")
        file1.write("Aug = " + x + "\n")
        x = input("Enter the September trailer path:")
        file1.write("Sep = " + x + "\n")
        x = input("Enter the October trailer path:")
        file1.write("Oct = " + x + "\n")
        x = input("Enter the November trailer path:")
        file1.write("Nov = " + x + "\n")
        x = input("Enter the December trailer path:")
        file1.write("Dec = " + x + "\n\n")
        file1.write("[PATHS]\n")
        x = input("Enter the Host directory path: (Path where your PreRoll folders are located)")
        file1.write("host_dir = " + x + "\n")
        x = input("OPTIONAL: Enter the Docker directory path: (Path where your PreRoll folders are located when using docker. (Path that Plex uses))")
        file1.write("docker_dir = " + x + "\n")
        logging.info('config file (config.ini) created')
        file1.close()

    config = ConfigParser()
    config.read(os.path.split(os.path.abspath(__file__))[0]+'/config.ini')
    configdict = {}

    if 'SERVER' in config:
        if 'plex_url' in config['SERVER']:
            configdict['plex_url'] = config.get('SERVER', 'plex_url')
        else:
            logging.error('Plex URL not found. Please update your config.')
            raise SystemExit
        if 'plex_token' in config['SERVER']:
            configdict['plex_token'] = config.get('SERVER', 'plex_token')
        else:
            logging.error('Plex token not found. Please update your config.')
            raise SystemExit     
    else:
        logging.error('Invalid config. SERVER not found. Please update your config.')
        raise SystemExit


    if 'PATHS' in config:
        if 'host_dir' in config['PATHS']:
            host_dir = os.path.join(config.get('PATHS', 'host_dir'),'')
            if 'docker_dir' in config['PATHS'] and config.get('PATHS', 'docker_dir'):
                docker_dir = os.path.join(config.get('PATHS', 'docker_dir'),'')
            else:
                docker_dir = host_dir
        else:
            logging.error('host_dir not found in config. Please update your config.')
            raise SystemExit
    else:
        logging.error('Invalid config. PATHS not found. Please update your config.')
        raise SystemExit
    
    for month in config['MONTHS']:
        path = config['MONTHS'][month].replace(docker_dir,host_dir)
        path = generatePreRoll(path).replace(host_dir,docker_dir)
        configdict[month] = path
    return configdict
    

#Automatically generate preroll based on a list of files in a folder
def generatePreRoll(PreRollPath):
    types = ['.mp4', '.avi', '.mkv']
    PreRollFiles = ''
    if any(type in PreRollPath for type in types):
        return PreRollPath
    else:
        PreRollPath = os.path.join(PreRollPath,'')
        for type in types:
            for file in os.listdir(PreRollPath):
                if file.endswith(type):
                    PreRollFiles+=os.path.join(PreRollPath, file)+';'
        return PreRollFiles

def main():
    # Arguments
    arguments = getArguments()
    configure_logging(arguments.log_level, arguments.log_file)
    show_banner()
    # Settings
    config = getConfig()
    if config['plex_url'] is not None: 
        session = requests.Session()
        session.verify = False
        requests.packages.urllib3.disable_warnings()
        url = str(config['plex_url'])
        token = str(config['plex_token'])
        plex = PlexServer(url, token, session, timeout=None)
        currentMonth = datetime.today().strftime('%b').lower()
        if currentMonth in config:
            plex.settings.get('cinemaTrailersPrerollID').set(config[currentMonth])
            plex.settings.save()
            logging.info(f'Pre-roll updated to {config[currentMonth]}')
        else:
            logging.warning(f'{currentMonth} not found in config. Please update your config. Pre-Roll not updated.')

if __name__ == '__main__':
    main()
    #getConfig()
