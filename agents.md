# Contributor Guide

## Dependencies

### Requirements.txt
Keep requirements.txt up to date with all requirements that are added.

### OpenAI API
For the love of all that's holy, use the latest OpenAI API. You can find an API definition here - https://github.com/openai/openai-python/blob/main/api.md - please refer to it for any task involving the OpenAI API. 

## Airtable Schema
Your setup script will pull down airtable schemas for all airtable bases and table you will need to read and write from and place them in airtable_schema.json. Refer to the schema when writing code to read from or write to airtable.

## Style
Wherever possible, pull logic out into unit testable functions and unit test them. 

## Testing
Run all unit tests before generating a commit.

## Commenting
Comment the code well. Comments should explain why the code is doing what it's doing, not what. Use information from the prompt and other available context to explain this. 
All Python methods should have docstrings that briefly explain what the method does, what its inputs are, and what its outputs are.

## PR instructions
Title format: [<project_name>] <Title>
