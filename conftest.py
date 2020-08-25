from pytest_astropy_header.display import (PYTEST_HEADER_MODULES,
                                           TESTED_VERSIONS)


def pytest_configure(config):
    config.option.astropy_header = True

    # https://github.com/PyGithub/PyGithub/issues/1600
    # PYTEST_HEADER_MODULES['PyGithub'] = 'github'

    PYTEST_HEADER_MODULES.pop('Pandas', None)
    PYTEST_HEADER_MODULES.pop('Matplotlib', None)
    PYTEST_HEADER_MODULES.pop('h5py', None)


TESTED_VERSIONS['bugbot'] = 'dev'
