# HITD Maps - Root Makefile
# ==========================
# Forwards commands to data-pipeline/Makefile
#
# Usage: make <target>
#

SHELL := /bin/bash
DATA_PIPELINE := data-pipeline

.PHONY: help auto-fix auto-fix-continuous auto-fix-stats learning-report \
        dashboard issues agent status pipeline

# Default - show help
help:
	@$(MAKE) -C $(DATA_PIPELINE) help

# Auto-fix commands
auto-fix:
	@$(MAKE) -C $(DATA_PIPELINE) auto-fix

auto-fix-continuous:
	@$(MAKE) -C $(DATA_PIPELINE) auto-fix-continuous INTERVAL=$(INTERVAL)

auto-fix-stats:
	@$(MAKE) -C $(DATA_PIPELINE) auto-fix-stats

learning-report:
	@$(MAKE) -C $(DATA_PIPELINE) learning-report

# Monitoring commands
dashboard:
	@$(MAKE) -C $(DATA_PIPELINE) dashboard

issues:
	@$(MAKE) -C $(DATA_PIPELINE) issues

issues-export:
	@$(MAKE) -C $(DATA_PIPELINE) issues-export

# Agent commands
agent:
	@$(MAKE) -C $(DATA_PIPELINE) agent

agent-once:
	@$(MAKE) -C $(DATA_PIPELINE) agent-once

# Pipeline commands
status:
	@$(MAKE) -C $(DATA_PIPELINE) status

pipeline:
	@$(MAKE) -C $(DATA_PIPELINE) pipeline

update:
	@$(MAKE) -C $(DATA_PIPELINE) update

cleanup:
	@$(MAKE) -C $(DATA_PIPELINE) cleanup

# Forward any other target to data-pipeline
%:
	@$(MAKE) -C $(DATA_PIPELINE) $@
