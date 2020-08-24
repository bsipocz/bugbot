import json
import logging
import os
import sys

from baldrick.github.github_api import IssueHandler

BUGBOT_LABEL = 'runbugbot'


def main(debug=False):
    logger = logging.getLogger('bugbot')
    if debug:
        logger.setLevel(10)
        logger.addHandler(logging.StreamHandler(sys.stdout))

    # FIXME: Might need to set up GitHub API key as secret if anon access
    # gets rate limited. And have to see how to hook it up to baldrick API.

    gh_event_path = os.environ['GITHUB_EVENT_PATH']
    with open(gh_event_path) as fp:
        gh_event = json.load(fp)
    logger.debug(
        f'GitHub event: {json.dumps(gh_event, sort_keys=True, indent=4)}')

    repo_name = os.environ['GITHUB_REPOSITORY']
    logger.debug(f'Repo name: {repo_name}')

    issue_num = gh_event['number']
    logger.debug(f'Issue number: {issue_num}')
    issue_handler = IssueHandler(repo_name, issue_num)

    # No-op if special label not present -- runbugbot
    if BUGBOT_LABEL not in issue_handler.labels:
        logger.info(f'{BUGBOT_LABEL} not found, stopping')
        return

    # is this new issue? is this a new comment?

    # make sure author is a maintainer

    # grab code snippet

    # sanitize code snippet

    # pipe code snippet into shell script, inject code to disable internet

    # run shell script


if __name__ == '__main__':
    # TODO: Remove debug before pushing to production.
    main(debug=True)
