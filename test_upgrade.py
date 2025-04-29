import hashlib
import unittest
import workflow_upgrade as upgrade

class TestUpgrade(unittest.TestCase):
  def test_md5sum(self):
    content = 'this is a test'
    md5 = hashlib.md5()
    md5.update(content.encode())
    self.assertEqual(md5.hexdigest(), upgrade.md5sum(content))

  def test_upgrade_target_version(self):
    content = '''
    on:
    push:
      branches:
        - master
    pull_request:
      branches:
        - master
      paths-ignore:
        - 'azure/**'
    jobs:
      terraform:
        uses:  foo/bar.yml@v5.8.1  # comments are preserved
        with:
          runs-on: '["arc-amd64"]'
          reduced_plan_output: true
        secrets: inherit
    '''
    expected = '''
    on:
    push:
      branches:
        - master
    pull_request:
      branches:
        - master
      paths-ignore:
        - 'azure/**'
    jobs:
      terraform:
        uses:  foo/bar.yml@v6.0.0  # comments are preserved
        with:
          runs-on: '["arc-amd64"]'
          reduced_plan_output: true
        secrets: inherit
    '''
    output = upgrade.update_target_version(content, 'foo/bar.yml@v6.0.0')
    self.assertEqual(expected, output)

  def test_update_target_version_multiple_matches(self):
    content = '''
    uses:foo/bar.yml@v1.2.3#
    uses: goober@aa55eeff
    goober@aa55eeff
    '''
    expected = '''
    uses:foo/bar.yml@v2.0.0#
    uses: goober@v3.1.0
    goober@aa55eeff
    '''
    for target in ['foo/bar.yml@v2.0.0', 'goober@v3.1.0']:
      content = upgrade.update_target_version(content, target)
    self.assertEqual(expected, content)

if __name__ == '__main__':
  unittest.main()
