# Welcome to secureblue

Thanks for taking the time to look into helping out!
All contributions are appreciated! 
Please refer to our [Code of Conduct](/CODE_OF_CONDUCT.md) while you're at it!

Feel free to report issues as you find them!

# Contributing

All types of contributions are encouraged and valued. See the [Table of Contents](#table-of-contents) for different ways to help and details about how this project handles them. Please make sure to read the relevant section before making your contribution. It will make it a lot easier for us maintainers and smooth out the experience for all involved. The community looks forward to your contributions. 

> And if you like the project, but just don't have time to contribute, that's fine. There are other easy ways to support the project and show your appreciation, which we would also be very happy about:
> - Star the project
> - Tweet about it
> - Refer this project in your project's readme
> - Mention the project at local meetups and tell your friends/colleagues

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [I Have a Question](#i-have-a-question)
- [I Want To Contribute](#i-want-to-contribute)
- [Reporting Bugs](#reporting-bugs)
- [Pull Requests](#pull-requests)
- [How to test incoming changes](#how-to-test-incoming-changes)
- [Building Locally](#building-locally)
- [Styleguides](#styleguides)
- [Commit Messages](#commit-messages)
- [Join The Project Team](#join-the-project-team)

## Code of Conduct

This project and everyone participating in it is governed by the
[CONTRIBUTING.md Code of Conduct](/CODE_OF_CONDUCT.md).
By participating, you are expected to uphold this code. Please report unacceptable behavior
to secureblueadmin@proton.me

## I Have a Question

> If you want to ask a question, ask in [Issues](https://github.com/secureblue/secureblue/issues).

## I Want To Contribute

> ### Legal Notice 
> When contributing to this project, you must agree that you have authored 100% of the content, that you have the necessary rights to the content and that the content you contribute may be provided under the project license.

### Reporting Bugs

#### Before Submitting a Bug Report

A good bug report should describe the issue in detail. Generally speaking:

- Make sure that you are using the latest version.
- Remember that these are unofficial builds, it's usually prudent to investigate an issue before reporting it here or in Fedora!
- Collect information about the bug:
  - `rpm-ostree status -v` usually helps
- Image and Version 
- Possibly your input and the output
- Can you reliably reproduce the issue? And can you also reproduce it with older versions?

### Pull Requests

#### Before Submitting a Pull Request

A good pull request should be ready for review before it is even created. For all pull requests, ensure:

- You have no unnecessary changes, including whitespace changes
- You have tested your changes
- For substantive changes, you include evidence of proper functionality in the pull request in addition to the build results.
- Your commits are [verified](https://docs.github.com/en/authentication/managing-commit-signature-verification)

### How to test incoming changes

One of the nice things about the image model is that we can generate an entire OS image for every change we want to commit, so this makes testing way easier than in the past. You can rebase to it, see if it works, and then move back. This also means we can increase the amount of testers! 

We strive towards a model where proposed changes are more thoroughly reviewed and tested by the community. So here's how to do it. If you see a pull request that is opened up on an image you're following you can leave a review on how it's working for you.

## Building Locally

The minimum tools required are git and a working machine with podman enabled and configured. 
Building locally is much faster than building in GitHub and is a good way to move fast before pushing to a remote.

### Clone the repo

    git clone https://github.com/secureblue/secureblue.git

### Build the image
    
First make sure you can build an existing image: 
    
    podman build . -t something
    
Then confirm your image built:
    
    podman image ls 

TODO: Set up and push to your own local registry
    
### Make your changes

This usually involved editing the `Containerfile`. Most techniques for building containers apply here, if you're new to containers using the term "Dockerfile" in your searches usually shows more results when you're searching for information. 

Check out CoreOS's [layering examples](https://github.com/coreos/layering-examples) for more information on customizing. 

## Styleguides
### Commit Messages

We use [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) and enforce them with a bot to keep the changelogs tidy:

```
chore: add Oyster build script
docs: explain hat wobble
feat: add beta sequence
fix: remove broken confirmation message
refactor: share logic between 4d3d3d3 and flarhgunnstow
style: convert tabs to spaces
test: ensure Tayne retains clothing
```

## Attribution
This guide is based on the **contributing.md**. [Make your own](https://contributing.md/)!
