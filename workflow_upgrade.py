import github
import os
import sys
import yaml

def get_client(token):
  try:
    auth = github.Auth.Token(token)
    client = github.Github(auth=auth)
    return client, None
  except github.GithubException.BadCredentialsException:
     return None, 'Unable to authenticate with provided credentials'

def get_repo(client, repo_name):
    repo = client.get_repo(repo_name)
    if repo is None:
      return None, f'Unable to access repo: {repo_name}'
    return repo, None

def get_workflow_content_files(repo):
  content_files = []
  contents = repo.get_contents('.github/workflows/')
  for c in contents:
    if (c.name.endswith('.yml') or c.name.endswith('.yaml')) and c.type == 'file':
      content_files.append(c)
  return content_files, None

def update_versions(content_file, library_name, target_version):
  pass

def branch_stuff():
    branches = [x.name for x in repo.get_branches()]
    branch_name = 'testbranch'
    if 'targetbranch' in branches:
      return True, f'targetbranch already exists in repo: {repo.name}'
    print(f'branches: {branches}')
    # get the main/master branch, will need ref for creating branch from
    primary_branch = set(['main', 'master']).intersection(set(branches))
    print(f'primary_branch: {primary_branch}')
    return False, None

def main(env_token, repos=['corey-d/workflowtest']):
  token = os.getenv(env_token)
  if token is None:
    sys.stderr.write(f'Empty environment variable: {env_token}\n')
    exit(1)
  client, err_msg = get_client(token)
  if client is None:
    sys.stderr.write(f'Error instantiating github client: {err_msg}\n')
    exit(1)
  failed_repos = []
  for repo_name in repos:
    print(f'Starting processing on repo: {repo_name}')
    repo, err_msg = get_repo(client, repo_name)
    if repo is None:
      sys.stderr.write(f'Error processing {repo_name}: {err_msg}\n')
      failed_repos.append(repo_name)
      continue
    workflow_content_files, err_msg = get_workflow_content_files(repo)
    for content_file in workflow_content_files:
      print(f'processing content file: {content_file}')
      update_versions(content_file, library_name, target_version)

    #try:
    ##  branch = repo.get_branch(branch_name)
    #  print(branch)
    #except github.GithubException.GithubException:

    #if branch is None:
    #  branch = repo.create_git_ref(branch_name)
    #contents = repo.get_contents('README.md', ref)

    #repo.update_file(path=contents.path, message='updating', content='This is a test', sha=contents.sha, branch=ref)


if __name__ == '__main__':
  import argparse
  parser = argparse.ArgumentParser(description='Update workflow 3rd party actions to specific version',
                                  epilog='㋡ Have a nice day! ㋡')
  parser.add_argument('-e', '--env-token', default='GITHUB_TOKEN', help='Environment variable name that has the GITHUB authentication token')
  parser.add_argument('-r', '--repo', default='corey-d/workflowtest', help='name of repo to process')
  parser.add_argument('--debug', action='store_true', help='enable github library built-in debug logging. SPAMMY.')

  args = parser.parse_args()
  if args.debug:
    github.enable_console_debug_logging()
  main(args.env_token, [args.repo])
