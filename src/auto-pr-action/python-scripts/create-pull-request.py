#!/usr/bin/env python3
''' Create Pull Request '''
import json
import os
import random
import string
import sys
import requests
from git import Repo
from github import Github
from github import GithubException


def get_github_event(github_event_path):
    with open(github_event_path) as f:
        github_event = json.load(f)
    if bool(os.environ.get('DEBUG_EVENT')):
        print(os.environ['GITHUB_EVENT_NAME'])
        print(json.dumps(github_event, sort_keys=True, indent=2))
    return github_event


def get_head_short_sha1(repo):
    return repo.git.rev_parse('--short', 'HEAD')


def get_random_suffix(size=7, chars=string.ascii_lowercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))


def remote_branch_exists(repo, branch):
    for ref in repo.remotes.origin.refs:
        if ref.name == ("origin/%s" % branch):
            return True
    return False


def get_author_default(event_name, event_data):
    if event_name == "push":
        email = "{head_commit[author][email]}".format(**event_data)
        name = "{head_commit[author][name]}".format(**event_data)
    else:
        email = os.environ['GITHUB_ACTOR'] + '@users.noreply.github.com'
        name = os.environ['GITHUB_ACTOR']
    return email, name


def set_git_config(git, email, name):
    git.config('--global', 'user.email', '"%s"' % email)
    git.config('--global', 'user.name', '"%s"' % name)


def set_git_remote_url(git, token, github_repository):
    git.remote(
        'set-url', 'origin', "https://x-access-token:%s@github.com/%s" %
        (token, github_repository))


def checkout_branch(git, remote_exists, branch):
    if remote_exists:
        git.stash('--include-untracked')
        git.checkout(branch)
        try:
            git.stash('pop')
        except BaseException:
            git.checkout('--theirs', '.')
            git.reset()
    else:
        git.checkout('HEAD', b=branch)


def cs_string_to_list(input_str):
    # Split the comma separated string into a list
    l = [i.strip() for i in input_str.split(',')]
    # Remove empty strings
    return list(filter(None, l))


def update_pull_request(pusher_name, github_token, repo_owner, github_repository,
                        pr_number, payload):
    patch_url = "https://api.github.com/repos/:{}/:{}/pulls/:{}".format(
        repo_owner, github_repository, pr_number)
    resp = requests.patch(patch_url, auth=(
        pusher_name, github_token), json=payload)
    print(resp.json())
    return resp


def process_event(github_token, github_repository, branch, base, pusher_name, repo_owner):
    title = os.getenv(
        'PULL_REQUEST_TITLE',
        "Auto-generated by create-pull-request action")
    body = os.getenv(
        'PULL_REQUEST_BODY', "Auto-generated pull request by "
        "[create-pull-request](https://github.com/dandu1008/auto-pr-github-action) GitHub Action")
    # Fetch optional environment variables with no default values
    pull_request_labels = os.environ.get('PULL_REQUEST_LABELS')
    pull_request_assignees = os.environ.get('PULL_REQUEST_ASSIGNEES')
    pull_request_milestone = os.environ.get('PULL_REQUEST_MILESTONE')
    pull_request_reviewers = os.environ.get('PULL_REQUEST_REVIEWERS')
    pull_request_team_reviewers = os.environ.get('PULL_REQUEST_TEAM_REVIEWERS')

    # Create the pull request
    print("Creating Pull Request for {} with reference base to {}".format(branch, base))
    github_repo = Github(github_token).get_repo(github_repository)
    try:
        pull_request = github_repo.create_pull(
            title=title,
            body=body,
            base=base,
            head=branch)
        print("Created pull request #%d (%s => %s)" %
              (pull_request.number, branch, base))
    except GithubException as e:
        print(e)
        if e.status == 422:
            # Format the branch name
            head_branch = "%s:%s" % (github_repository.split("/")[0], branch)
            # Get the pull request
            pull_request = github_repo.get_pulls(
                state='open',
                base=base,
                head=head_branch)[0]
            if pull_request.number:
                payload = {
                    "title": title,
                    "body": body,
                    "state": 'open',
                    "base": base,
                }
                update_pull_request(
                    pusher_name, github_token, repo_owner, github_repository, pull_request.number, payload)
            print("Updated pull request #%d (%s => %s)" %
                  (pull_request.number, branch, base))
        else:
            print(str(e))
            sys.exit(1)

    # Set the output variables
    os.system(
        'echo ::set-env name=PULL_REQUEST_NUMBER::%d' %
        pull_request.number)
    os.system(
        'echo ::set-output name=pr_number::%d' %
        pull_request.number)

    # Set labels, assignees and milestone
    if pull_request_labels is not None:
        print("Applying labels")
        pull_request.as_issue().edit(labels=cs_string_to_list(pull_request_labels))
    if pull_request_assignees is not None:
        print("Applying assignees")
        pull_request.as_issue().edit(assignees=cs_string_to_list(pull_request_assignees))
    if pull_request_milestone is not None:
        print("Applying milestone")
        milestone = github_repo.get_milestone(int(pull_request_milestone))
        pull_request.as_issue().edit(milestone=milestone)

    # Set pull request reviewers
    if pull_request_reviewers is not None:
        print("Requesting reviewers")
        try:
            pull_request.create_review_request(
                reviewers=cs_string_to_list(pull_request_reviewers))
        except GithubException as e:
            # Likely caused by "Review cannot be requested from pull request author."
            if e.status == 422:
                print("Requesting reviewers failed - %s" % e.data["message"])

    # Set pull request team reviewers
    if pull_request_team_reviewers is not None:
        print("Requesting team reviewers")
        pull_request.create_review_request(
            team_reviewers=cs_string_to_list(pull_request_team_reviewers))


def main():
    # Fetch environment variables
    print("Python process is initiated")
    github_token = os.environ['GITHUB_TOKEN']
    github_repository = os.environ['GITHUB_REPOSITORY']
    event_name = os.environ['GITHUB_EVENT_NAME']
    # Get the JSON event data
    event_data = get_github_event(os.environ['GITHUB_EVENT_PATH'])
    print(event_data)
    # Set the repo to the working directory
    repo = Repo(os.getcwd())
    # Get the default for author email and name
    author_email, author_name = get_author_default(event_name, event_data)
    # Set commit author overrides
    author_email = os.getenv('COMMIT_AUTHOR_EMAIL', author_email)
    author_name = os.getenv('COMMIT_AUTHOR_NAME', author_name)
    # Set git configuration
    set_git_config(repo.git, author_email, author_name)
    # Update URL for the 'origin' remote
    set_git_remote_url(repo.git, github_token, github_repository)
    # Fetch/Set the branch name
    branch = os.getenv(
        'PULL_REQUEST_BRANCH',
        'create-pull-request/patch')
    base = "{repository[default_branch]}".format(**event_data)
    pusher_name = "{pusher[name]}".format(**event_data)
    repo_owner = "{repository[owner][name]}".format(**event_data)
    # Check if the remote branch exists
    remote_exists = remote_branch_exists(repo, branch)
    # Checkout branch
    checkout_branch(repo.git, remote_exists, branch)
    # Check if there are changes to pull request
    process_event(
        github_token,
        github_repository,
        branch,
        base,
        pusher_name,
        repo_owner)


if __name__ == '__main__':
    main()
