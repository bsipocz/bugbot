import json
import logging
import os
import sys

from github import Github

__all__ = []

BUGBOT_LABEL = 'runbugbot'
BUGBOG_TITLE = '**run bugbot run**'
BUGBOT_FILENAME = 'test_me.py'


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

    repo_name = gh_event['repository']['full_name']
    repo_handler = pygh.get_repo(repo_name)
    logger.debug(f'Repo name: {repo_name}')

    issue_num = gh_event['issue']['number']
    issue_handler = repo_handler.get_issue(number=issue_num)
    logger.debug(f'Issue number: {issue_num}')

    # No-op if special label not present
    # NOTE: Strictly speaking, you can extract this out of gh_event without
    # using PyGithub, but we need PyGithub to check membership later anyway,
    # so might as well.
    if not any([BUGBOT_LABEL in s.name for s in issue_handler.labels]):
        logger.info(f'{BUGBOT_LABEL} not found, stopping')
        return

    # TODO: Make sure author is a maintainer -- Need authenticated access
    # when initializing Github() above.
    # A hack without needing auth might be keeping a list as Actions
    # secret but the maintenance and security implications need understanding.
    author_name = gh_event['sender']['login']

    if 'comment' in gh_event:  # New comment on existing issue
        logger.debug(f'Comment author: {author_name}')
        body_content = gh_event['comment']['body']
    else:  # New issue
        logger.debug(f'Issue author: {author_name}')
        body_content = gh_event['issue']['body']

    # Grab code snippet and disable internet.
    raw_code = get_code_snippet(body_content)
    if len(raw_code) == 0:
        logger.info(f'No code found in {body_content}, stopping')
        return
    code_lines = inject_no_internet(raw_code)

    # TODO: Sanitize code snippet.

    # Write code snippet into shell script.
    with open(BUGBOT_FILENAME, 'w') as fp:
        for line in code_lines:
            fp.write(line + os.linesep)

    logger.info(f'Run "pytest {BUGBOT_FILENAME}" to test code.')

    # TODO: Need authenticated access when initializing Github() above.
    # Post a comment to the issue.
    # logger.debug('Attempting to post a comment')
    # issue_handler.create_comment(
    #     f'Hello, I am bug bot. '
    #     f'Please check https://github.com/{repo_name}/actions')


def get_code_snippet(body_content):
    """Extract code snippet from well-behaved body content from GitHub event
    context. Body content is all one string.

    Example::

        A test comment to trigger Actions with code snippet.

        **Run bugbot run**

        ```python
        x = [1, 2, 3]
        assert sum(x) == 5  # Doesn't work, halp
        ```

    """
    # Body has \r\n
    lines = [s.strip('\r') for s in body_content.split(os.linesep)]
    code_markdown = '```'
    code_lines = []
    found_incantation = False

    # Ignore everything before special incantation (case-insensitive)
    for s in lines:
        if found_incantation and not s.startswith(code_markdown):
            code_lines.append(s)
        elif s.strip().lower() == BUGBOG_TITLE:
            found_incantation = True

    return code_lines


def inject_no_internet(code_lines):
    """Disable internet for the given code lines and turn them into
    test function.
    """
    # TODO: For production, no_internet needs to come from a proper package.
    # TODO: What if code is not written in a way that is compatible with
    # pytest testing?
    indent = '        '
    injected_code = [
        'from pytest_remotedata.disable_internet import no_internet',
        '', '',
        'def test_this_snippet():',
        '    with no_internet():']
    for line in code_lines:
        if line:
            injected_code.append(indent + line)
        else:
            injected_code.append(line)

    return injected_code


if __name__ == '__main__':
    # TODO: Remove debug before pushing to production.
    main(debug=True)
