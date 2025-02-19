// Copyright 2024 secureblue
//
// This file includes code from https://github.com/peternied/required-approval which is licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS"
// BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language
// governing permissions and limitations under the License.


const core = require("@actions/core");
const github = require("@actions/github");

async function run() {
  const token = core.getInput('token', { required: true });
  if (!token) {
    core.setFailed(`Input parameter 'token' is required`);
    return;
  }

  const minRequiredStr = core.getInput('min-required', { required: true })
  if (!minRequiredStr) {
    core.setFailed(`Input parameter 'min-required' is required`);
    return;
  }
  const minRequired = parseInt(minRequiredStr, 10);

  const pullRequestId = github.context.payload.pull_request?.number;
  if (!pullRequestId) {
    core.setFailed(`Unable to find associated pull request from the context: ${JSON.stringify(github.context)}`);
    return;
  }

  const approversString = core.getInput('approvers', { required: true });
  const approvers = approversString.split('\n').map(s => s.trim());

  const client = github.getOctokit(token);
  const allReviews = await client.paginate.iterator(client.rest.pulls.listReviews, {
      pull_number: pullRequestId,
      owner: github.context.repo.owner,
      repo: github.context.repo.repo,
      per_page: 100,
  });

  let validApprovers = new Set();
  for await (const { data: reviews } of allReviews) {
      for (const review of reviews) {
        const userId = review.user?.login;
        if (review.state === 'APPROVED' && userId) {
            if (approvers.includes(userId)) {
                validApprovers.add(userId);
            }
        }
     }
  }

  if (validApprovers.size > 0) {
    core.info(`Found approvals from ${[...validApprovers].join(', ')}`);
  } else {
    core.info("No approvals found.")
  }

  if (validApprovers.size < minRequired) {
    core.setFailed(`Not enough approvals; has ${validApprovers.size} where ${minRequired} approvals are required.`);
  } else {
    core.info(`Meets minimum number of approvals requirement with ${validApprovers.size} approvals`);
  }
}

run();