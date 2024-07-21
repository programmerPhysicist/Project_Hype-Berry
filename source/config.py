'''This file deals with config related functions'''
import logging
import configparser
import sys

# TODO: Do a proper refactor of these functions


def get_todoist_token(configfile):
    """Get Todoist token from the auth.cfg file."""
    logging.debug('Loading todoist auth data from %s', configfile)

    config = configparser.ConfigParser()
    config.read(configfile)

    # Get data from config
    if 'Todoist' in config.sections():
        try:
            tt = config.get('Todoist', 'api-token')

        except configparser.NoOptionError as e:
            logging.error("Missing option in auth file '" + configfile + "': " + e.message)
            sys.exit(1)
    else:
        logging.error("No 'Todoist' section in '%s'", configfile)
        sys.exit(1)

    return tt


def get_habitica_login(configfile):
    """Get Habitica authentication data from the auth.cfg file."""

    logging.debug('Loading habitica auth data from %s', configfile)

    config = configparser.ConfigParser()
    config.read(configfile)

    # Get data from config
    rv = {}
    if 'Habitica' in config.sections():
        try:
            rv = {'url': config.get('Habitica', 'url'),
                  'x-api-user': config.get('Habitica', 'login'),
                  'x-api-key': config.get('Habitica', 'password')}

        except configparser.NoOptionError as e:
            logging.error("Missing option in auth file " + configfile + ":" + e.message)
            sys.exit(1)
    else:
        logging.error("No 'Habitica' section in '%s'", configfile)
        sys.exit(1)

    # Return auth data as a dictionnary
    return rv
