'''This file deals with config related functions'''
import logging
import configparser


def getTodoistToken(configfile):
    logging.debug('Loading todoist auth data from %s' % configfile)

    try:
        cf = open(configfile)
    except IOError:
        logging.error("Unable to find '%s'." % configfile)
        exit(1)

    config = configparser.SafeConfigParser()
    config.readfp(cf)

    cf.close()

    # Get data from config
    try:
        tt = config.get('Todoist', 'api-token')

    except configparser.NoSectionError:
        logging.error("No 'Todoist' section in '%s'" % configfile)
        exit(1)

    except configparser.NoOptionError as e:
        logging.error("Missing option in auth file '%s': %s" % (configfile, e.message))
        exit(1)

    return tt

def get_started(configfile):
    """Get Habitica authentication data from the AUTH_CONF file."""

    logging.debug('Loading habitica auth data from %s' % configfile)

    try:
        cf = open(configfile)
    except IOError:
        logging.error("Unable to find '%s'." % configfile)
        exit(1)

    config = configparser.SafeConfigParser()
    config.readfp(cf)

    cf.close()

    # Get data from config
    rv = {}
    try:
        rv = {'url': config.get('Habitica', 'url'),
              'x-api-user': config.get('Habitica', 'login'),
              'x-api-key': config.get('Habitica', 'password')}

    except configparser.NoSectionError:
        logging.error("No 'Habitica' section in '%s'" % configfile)
        exit(1)

    except configparser.NoOptionError as e:
        logging.error("Missing option in auth file '%s': %s"
                      % (configfile, e.message))
        exit(1)

    # Return auth data as a dictionnary
    return rv