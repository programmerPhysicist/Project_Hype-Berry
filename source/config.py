'''This file deals with config related functions'''
import logging
import configparser
import sys


def get_todoist_token(configfile):
    """Get Todoist token from the auth.cfg file."""
    logging.debug('Loading todoist auth data from %s', configfile)

    config = configparser.ConfigParser()
    config.read(configfile)

    # Get data from config
    if 'Todoist' in config.sections():
        try:
            todo_token = config.get('Todoist', 'api-token')

        except configparser.NoOptionError as error:
            logging.error("Missing option in auth file '" + configfile + "': " + error.message)
            sys.exit(1)
    else:
        logging.error("No 'Todoist' section in '%s'", configfile)
        sys.exit(1)

    return todo_token


def get_habitica_login(configfile):
    """Get Habitica authentication data from the auth.cfg file."""

    logging.debug('Loading habitica auth data from %s', configfile)

    config = configparser.ConfigParser()
    config.read(configfile)

    # Get data from config
    auth_data = {}
    if 'Habitica' in config.sections():
        try:
            auth_data = {'url': config.get('Habitica', 'url'),
                         'x-api-user': config.get('Habitica', 'login'),
                         'x-api-key': config.get('Habitica', 'password')}
            
            auth_data['X-Client'] = '518b34ec-0992-457d-a6cb-58e5bd20f522-ProjectHypeBerry'

        except configparser.NoOptionError as error:
            logging.error("Missing option in auth file " + configfile + ":" + error.message)
            sys.exit(1)
    else:
        logging.error("No 'Habitica' section in '%s'", configfile)
        sys.exit(1)

    # Return auth data as a dictionary
    return auth_data
