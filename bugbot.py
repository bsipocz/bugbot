import json
import logging
import os
import sys

from github import Github

__all__ = []

BUGBOT_LABEL = 'runbugbot'


def main(debug=False):
    logger = logging.getLogger('bugbot')
    if debug:
        logger.setLevel(10)
        logger.addHandler(logging.StreamHandler(sys.stdout))

    # FIXME: Might need to set up GitHub API key as secret if anon access
    # gets rate limited.
    pygh = Github()

    gh_event_path = os.environ['GITHUB_EVENT_PATH']
    with open(gh_event_path) as fp:
        gh_event = json.load(fp)
    logger.debug(
        f'GitHub event: {json.dumps(gh_event, sort_keys=True, indent=4)}')

    repo_name = os.environ['GITHUB_REPOSITORY']
    repo_handler = pygh.get_repo(repo_name)
    logger.debug(f'Repo name: {repo_name}')

    issue_num = gh_event['number']
    issue_handler = repo_handler.get_issue(number=issue_num)
    logger.debug(f'Issue number: {issue_num}')

    # No-op if special label not present
    if not any([BUGBOT_LABEL in s.name for s in issue_handler.labels]):
        logger.info(f'{BUGBOT_LABEL} not found, stopping')
        return

    # is this new issue? is this a new comment?

    # TODO: Make sure author is a maintainer -- Need authenticated access
    # author_name = gh_event['sender']['login']
    # logger.debug(f'Issue author: {author_name}')

    # grab code snippet

    # sanitize code snippet

    # pipe code snippet into shell script, inject code to disable internet
    # TODO: Use no_internet defined below.

    # run shell script


# These functions are copied from pytest-remotedata, with Astropy stuff
# stripped, because it does not make sense to have the bot be dependent on
# a pytest plugin with Astropy settings.

import contextlib  # noqa: E402
import socket  # noqa: E402
import urllib  # noqa: E402

# save original socket method for restoration
# These are global so that re-calling the turn_off_internet function doesn't
# overwrite them again
socket_original = socket.socket
socket_create_connection = socket.create_connection
socket_bind = socket.socket.bind
socket_connect = socket.socket.connect

INTERNET_OFF = False

# urllib uses a global variable to cache its default "opener" for opening
# connections for various protocols; we store it off here so we can restore to
# the default after re-enabling internet use
_orig_opener = None


def _resolve_host_ips(hostname, port=80):
    """
    Obtain all the IPs, including aliases, in a way that supports
    IPv4/v6 dual stack.
    """
    try:
        ips = set([s[-1][0] for s in socket.getaddrinfo(hostname, port)])
    except socket.gaierror:
        ips = set([])

    ips.add(hostname)
    return ips


# ::1 is apparently another valid name for localhost?
# it is returned by getaddrinfo when that function is given localhost

def check_internet_off(original_function):
    """
    Wraps ``original_function``, which in most cases is assumed
    to be a `socket.socket` method, to raise an `IOError` for any operations
    on non-local AF_INET sockets.
    """

    def new_function(*args, **kwargs):
        if isinstance(args[0], socket.socket):
            if not args[0].family in (socket.AF_INET, socket.AF_INET6):
                # Should be fine in all but some very obscure cases
                # More to the point, we don't want to affect AF_UNIX
                # sockets.
                return original_function(*args, **kwargs)
            host = args[1][0]
            addr_arg = 1
            valid_hosts = set(['localhost', '127.0.0.1', '::1'])
        else:
            # The only other function this is used to wrap currently is
            # socket.create_connection, which should be passed a 2-tuple, but
            # we'll check just in case
            if not (isinstance(args[0], tuple) and len(args[0]) == 2):
                return original_function(*args, **kwargs)

            host = args[0][0]
            addr_arg = 0
            valid_hosts = set(['localhost', '127.0.0.1'])

        hostname = socket.gethostname()
        fqdn = socket.getfqdn()

        if host in (hostname, fqdn):
            host = 'localhost'
            host_ips = set([host])
            new_addr = (host, args[addr_arg][1])
            args = args[:addr_arg] + (new_addr,) + args[addr_arg + 1:]
        else:
            host_ips = _resolve_host_ips(host)

        if len(host_ips & valid_hosts) > 0:  # Any overlap is acceptable
            return original_function(*args, **kwargs)
        else:
            raise IOError("An attempt was made to connect to the internet. "
                          f"The requested host was: {host}")
    return new_function


def turn_off_internet(verbose=False):
    """
    Disable internet access via python by preventing connections from being
    created using the socket module.  Presumably this could be worked around by
    using some other means of accessing the internet, but all default python
    modules (urllib, requests, etc.) use socket [citation needed].
    """

    global INTERNET_OFF
    global _orig_opener

    if INTERNET_OFF:
        return

    INTERNET_OFF = True

    __tracebackhide__ = True
    if verbose:
        print("Internet access disabled")

    # Update urllib to force it not to use any proxies
    # Must use {} here (the default of None will kick off an automatic search
    # for proxies)
    _orig_opener = urllib.request.build_opener()
    no_proxy_handler = urllib.request.ProxyHandler({})
    opener = urllib.request.build_opener(no_proxy_handler)
    urllib.request.install_opener(opener)

    socket.create_connection = check_internet_off(socket_create_connection)
    socket.socket.bind = check_internet_off(socket_bind)
    socket.socket.connect = check_internet_off(socket_connect)

    return socket


def turn_on_internet(verbose=False):
    """Restore internet access."""

    global INTERNET_OFF
    global _orig_opener

    if not INTERNET_OFF:
        return

    INTERNET_OFF = False

    if verbose:
        print("Internet access enabled")

    urllib.request.install_opener(_orig_opener)

    socket.create_connection = socket_create_connection
    socket.socket.bind = socket_bind
    socket.socket.connect = socket_connect
    return socket


@contextlib.contextmanager
def no_internet(verbose=False):
    """Context manager to temporarily disable internet access (if not already
    disabled).  If it was already disabled before entering the context manager
    (i.e. `turn_off_internet` was called previously) then this is a no-op and
    leaves internet access disabled until a manual call to `turn_on_internet`.
    """

    already_disabled = INTERNET_OFF

    turn_off_internet(verbose=verbose)
    try:
        yield
    finally:
        if not already_disabled:
            turn_on_internet(verbose=verbose)


if __name__ == '__main__':
    # TODO: Remove debug before pushing to production.
    main(debug=True)
