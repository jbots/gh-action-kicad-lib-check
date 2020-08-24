FROM python:3.8

ADD run_checks.sh kicad_to_github_actions.py /
RUN chmod +x /run_checks.sh
ENTRYPOINT ["/run_checks.sh"]
