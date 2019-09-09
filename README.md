# An example template for a Python package

Set up to be tested by Azure pipelines

### To register a new pipelines build:

If necessary, install the `az` command line tools and `devops` extension.

```
pip install --user azure-cli
az extension add devops
```

And register an account and/or organization on [Microsoft DevOps](https://dev.azure.com).

Then run the following incantation


```
az devops login --organization <organization_url e.g. https://dev.azure.com/jrper>
az devops project create --name <project_name>
az pipelines create --name <project_name> --repository <repo_url e.g. >
```

[![Build Status](https://dev.azure.com/jrper/python_project_template/_apis/build/status/python_project_template?branchName=master)](https://dev.azure.com/jrper/python_project_template/_build/latest?definitionId=6&branchName=master) [![Build Status](https://travis-ci.com/jrper/python_project_template.svg?branch=master)](https://travis-ci.com/jrper/python_project_template)
