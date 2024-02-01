#!/bin/bash

export PHOBO_ENV="production"
flask --app ./src/phobo/phobo --debug run --host=0.0.0.0 --port=8080