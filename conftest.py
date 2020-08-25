def pytest_report_header(config):
    import os

    deps = ['', 'Package versions: ']

    # Append dependency as needed.
    # https://github.com/PyGithub/PyGithub/issues/1600
    deps.append('PyGitHub: stable')

    deps.append('')
    return os.linesep.join(deps)
