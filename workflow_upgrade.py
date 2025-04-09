import base64
import copy
import github
import os
import re
import sys
import typing
import yaml

# type aliases for PEP-484 Type Hints
Branch = github.Branch
ContentFile = github.ContentFile.ContentFile
Github = github.Github
Repository = github.Repository.Repository

# "constants"
BASE64 = 'base64'
UTF8 = 'utf-8'

def get_client(token: str) -> [Github, str]:
  try:
    auth = github.Auth.Token(token)
    client = github.Github(auth=auth)
    return client, None
  except github.GithubException.BadCredentialsException:
     return None, 'Unable to authenticate with provided credentials'


def get_workflow_content_files(repo: Repository, branch: str) -> [ContentFile]:
  content_files = []
  contents = repo.get_contents('.github/workflows/', ref=branch)
  for c in contents:
    if (c.name.endswith('.yml') or c.name.endswith('.yaml')) and c.type == 'file':
      content_files.append(c)
  return content_files

def extract_content(content_file: ContentFile) -> dict:
  #content = content_file.content.encode(UTF8)
  #if content_file.encoding == BASE64:
  #  print(f'base64 decoding of content from {content_file.html_url}')
    # transformers tranforming WIXXWUXXWRRKWUXX noises here...
  #  content = base64.b64decode(content)
  return yaml.safe_load(content_file.decoded_content.decode(UTF8))

def update_content(repo: Repository, content_file: ContentFile, content: str) -> ContentFile:
  content = yaml.dump(content)
  if content_file.encoding == BASE64:
    content = base64.b64encode(content.encode(UTF8))
  print(f'CONTENT_FILE: {content_file}')
  content_file.content = content
  return content_file

# dictionaries are passed by reference
def update_target_version(content: dict, target_version: str):
  target_lib, _ = target_version.split('@')
  for job in content['jobs']:
    library = content['jobs'][job].get('uses', None)
    if library is None:
      continue
    print(f'uses: {library}')
    lib, _ = library.split('@')
    if lib == target_lib:
      content['jobs'][job]['uses'] = target_version

def main(env_token: str, repos: [str], target_libraries: [str]):
  if len(target_libraries) == 0:
    sys.stderr.write('No 3rd party actions provided. Exiting.')
    exit(1)
  token = os.getenv(env_token)
  if token is None:
    sys.stderr.write(f'Empty environment variable: {env_token}\n')
    exit(1)
  client, err_msg = get_client(token)
  if client is None:
    sys.stderr.write(f'Error instantiating github client: {err_msg}\n')
    exit(1)
  # fail-log auditing array to report out after the run
  failed_repos = []
  # iterate over all the repos and update as needed
  for repo_name in repos:
    print(f'Starting processing on repo: {repo_name}')
    repo = client.get_repo(repo_name)
    if repo is None:
      sys.stderr.write(f'Error processing {repo_name}: {err_msg}\n')
      failed_repos.append(repo_name)
      continue

    # check if the new branch needs to be made or not
    if 'update' not in [branch.name for branch in repo.get_branches()]:
      repo.create_git_ref(ref='refs/heads/update', sha=repo.get_branch(repo.default_branch).commit.sha)

    # the content files need to be grabbed referenced from the newly created branch
    workflow_content_files = get_workflow_content_files(repo, 'update')
    if not len(workflow_content_files):
      # this should probably be checked _before_ creating the branch
      print(f'no workflow files in repo: {repo.name}')
      continue

    # iterate through each found workflow file
    for content_file in workflow_content_files:
      print(f'processing workflow file: {content_file.name}')
      # FYI: content is stored base64 encoded, get the raw text
      content = yaml.safe_load(content_file.decoded_content.decode()) #extract_content(content_file)
      # stash the original content to see if there were any changes
      reference_content = copy.deepcopy(content)
      # it _might_ be worth having update_target_version take a list of targets
      # but that's for another day
      for target in target_libraries:
        print(f'working on target: {target}')
        update_target_version(content, target)

      if reference_content == content:
        print(f'No changes made to workflow file: {content_file.name}')
        continue

      content = yaml.dump(content)
      repo.update_file(path=content_file.path, content=content, sha=content_file.sha, branch='update', message=f'updating 3rd party actions')
      #commit_changes()
      print(f'content: {content}')


if __name__ == '__main__':
  import argparse

  # very basic validation of 3rd party library declarations
  def validate_target(target):
    if len(target.split('@')) != 2:
      raise argparse.ArgumentTypeError('must be in the form of `action-path@version`')
    return target

  def process_batch_file(filename: str) -> [list, list]:
    return ['a'],['b']


  parser = argparse.ArgumentParser(description='Update workflow 3rd party actions to specific version',
                                  epilog='㋡ Have a nice day! ㋡')
  # arguments common to all sub commands
  parser.add_argument('--debug', action='store_true', help='enable github library built-in debug logging. SPAMMY.')
  parser.add_argument('-e', '--env-token', default='GITHUB_TOKEN', help='Environment variable name that has the GITHUB authentication token')
  parser.add_argument('--bail', action='store_true')
  # we will split the arguments into two groups using subcommands
  sub_parser = parser.add_subparsers(help='commands')

  # manual mode for entering options on the command line, useful for a small set of repos
  manual = sub_parser.add_parser('manual', help='enter all options on the command line')
  manual.add_argument('repo', action='append')
  manual.add_argument('target', action='append', type=validate_target)
  manual.add_argument('-r', '--repo', action='append', dest='repo', help='additional repositories to process')
  manual.add_argument('-t', '--target', action='append', dest='target', type=validate_target)

  # batch will read a CSV of options, useful for larger groups of processing
  batch = sub_parser.add_parser('batch', help='read options in from csv file')
  batch.add_argument('filename', help='filename that has options in repo,action-name@version format')
  args = parser.parse_args()

  if args.debug:
    github.enable_console_debug_logging()
  if hasattr(args, 'filename'):
    args.repo, args.target = process_batch_file(args.filename)
  print(args)
  if args.bail:
    exit(0)
  main(args.env_token, args.repo, args.target)
