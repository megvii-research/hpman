# Contributing

First off, thank you for your interest in hpman.

All members of our community are expected to follow our the [
Code of Conduct](./CODE_OF_CONDUCT.md). Please make sure you are welcoming and friendly in all of our spaces.

## How to file a bug report

We were tracking bugs through GitHub issues.

### Make sure you're using the latest version.

You can view all the [releases](https://github.com/sshao0516/hpman/releases). Maybe the bug was fixed at the latest version.

### Determine if it is a bug. Not a feature.

Because we had some assumptions in the `hpman` design, please read the [design principles]() first. If it's not a bug, you can suggest new features.

### Check it's not a duplicate issue.

You can check [all open issues](https://github.com/sshao0516/hpman/issues). If the same bug has already been reported, you should add a comment to the current issue with more information.

### Using the template.

Collecting information about the bug. You should answer these five questions:

1. What version of `hpman` are you using?
2. What operating system and processor architecture are you using?
3. What did you do?
4. What did you expect to see?
5. What did you see instead?

Provide as much information as you can. You may think that the problem lies with your query when actually it depends on how your data is indexed. The easier it is for us to recreate your problem, the faster it is likely to be fixed.

### Submit the bug.

You should give it a `bug` label. Click `Submit new issue` button. Feel at ease.

## How to suggest an enhancement

Enhancement suggestions are welcome. However, take a moment to find out whether your idea fits with the scope and aims of the [design principles]() first.

Enhancement suggestions are tracked as GitHub issues.


### Make sure you're using the latest version.

You can view all the [releases](https://github.com/sshao0516/hpman/releases). Maybe the enhancement was implemented at the latest version.

### Check if there's already a plug-in which provides that enhancement.

- [hpargparse]() argparse extension for hpman.

### Provide details and reasons.

Please provide as much detail and context as possible.

You need strong reasons and background to convince others.


### Submit the enhancement.

You should give it an `enhancement` label. Click `Submit new issue` button.

Moreover, you can discuss with others, start developing, and submit a pull request.

## How to contribute code or documentation changes.

### Clone the repo and create a branch
```
git clone https://github.com/sshao0516/hpman
cd hpman
git checkout -b <topic-branch-name>
```
Using a clear and descriptive branch name.

### Setting up your environment
1. Install requirements:
```bash
pip install -r requirements.dev.txt
```

2. Install pre-commit hook
```bash
pre-commit install
```

### Running tests

3. To format your source code
```bash
make format
```

4. To check the coding style
```bash
make style-check
```

5. To run unit tests.
```bash
make test
```

### Creating a pull request

**Please ask first** before embarking on any significant pull request (e.g., implementing features, refactoring code). Otherwise, you risk spending much time working on something that the project's developers might not want to merge into the project.

Use a clear and descriptive title. And a detailed and accurate description of the changes. Waiting for the pass CI test.

Click "Create pull request".
