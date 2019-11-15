"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
require("module-alias/register");
require("source-map-support/register");
const sourceMapSupport = require("source-map-support");
const util_1 = require("util");
const core = require("@actions/core");
const exec = require("@actions/exec");
const setup_python_1 = require("./python-scripts/setup-python");
sourceMapSupport.install();
// Fetch action inputs
const inputs = {
    token: core.getInput("token"),
    commitMessage: core.getInput("commit-message"),
    commitAuthorEmail: core.getInput("author-email"),
    commitAuthorName: core.getInput("author-name"),
    title: core.getInput("title"),
    body: core.getInput("body"),
    labels: core.getInput("labels"),
    assignees: core.getInput("assignees"),
    reviewers: core.getInput("reviewers"),
    teamReviewers: core.getInput("team-reviewers"),
    milestone: core.getInput("milestone"),
    branch: core.getInput("branch"),
    base: core.getInput("base"),
    branchSuffix: core.getInput("branch-suffix"),
    debugEvent: core.getInput("debug-event")
};
// Set environment variables from inputs.
if (inputs.token)
    process.env.GITHUB_TOKEN = inputs.token;
if (inputs.commitMessage)
    process.env.COMMIT_MESSAGE = inputs.commitMessage;
if (inputs.commitAuthorEmail)
    process.env.COMMIT_AUTHOR_EMAIL = inputs.commitAuthorEmail;
if (inputs.commitAuthorName)
    process.env.COMMIT_AUTHOR_NAME = inputs.commitAuthorName;
if (inputs.title)
    process.env.PULL_REQUEST_TITLE = inputs.title;
if (inputs.body)
    process.env.PULL_REQUEST_BODY = inputs.body;
if (inputs.labels)
    process.env.PULL_REQUEST_LABELS = inputs.labels;
if (inputs.assignees)
    process.env.PULL_REQUEST_ASSIGNEES = inputs.assignees;
if (inputs.reviewers)
    process.env.PULL_REQUEST_REVIEWERS = inputs.reviewers;
if (inputs.teamReviewers)
    process.env.PULL_REQUEST_TEAM_REVIEWERS = inputs.teamReviewers;
if (inputs.milestone)
    process.env.PULL_REQUEST_MILESTONE = inputs.milestone;
if (inputs.branch)
    process.env.PULL_REQUEST_BRANCH = inputs.branch;
if (inputs.base)
    process.env.PULL_REQUEST_BASE = inputs.base;
if (inputs.branchSuffix)
    process.env.BRANCH_SUFFIX = inputs.branchSuffix;
if (inputs.debugEvent)
    process.env.DEBUG_EVENT = inputs.debugEvent;
async function run() {
    try {
        // Allows ncc to find assets to be included in the distribution
        const src = __dirname + "/python-scripts";
        core.debug(`src: ${src}`);
        // Setup Python from the tool cache
        setup_python_1.setupPython("3.8.0", "x64");
        // Install requirements
        await exec.exec("pip", ["install", "--requirement", `${src}/requirements.txt`]);
        core.debug(`Inputs: ${util_1.inspect(inputs)}`);
        // Execute python script
        await exec.exec("python", [`${src}/create-pull-request.py`]);
    }
    catch (error) {
        core.setFailed(error.message);
    }
}
run();
//# sourceMappingURL=index.js.map