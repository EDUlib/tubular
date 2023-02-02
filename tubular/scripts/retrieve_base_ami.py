#! /usr/bin/env python3

"""
Command-line script used to retrieve the last base AMI ID used for an environment/deployment/play.
"""
# pylint: disable=invalid-name

from os import path
import io
import sys
import logging
import traceback
import click
import yaml

# Add top-level module path to sys.path before importing tubular code.
sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))

from tubular import ec2  # pylint: disable=wrong-import-position

logging.basicConfig(level=logging.INFO)


@click.command()
@click.option(
    '--environment', '-e',
    help='Environment for AMI, e.g. prod, stage',
    required=True,
)
@click.option(
    '--deployment', '-d',
    help='Deployment for AMI e.g. edx, edge',
    required=True,
)
@click.option(
    '--play', '-p',
    help='Play for AMI, e.g. edxapp, insights, discovery',
    required=True,
)
@click.option(
    '--override',
    help='Override AMI id to use',
)
@click.option(
    '--out_file',
    help='Output file for the AMI information yaml.',
    default=None,
)
def retrieve_base_ami(environment, deployment, play, override, out_file):
    """
    Method used to retrieve the last base AMI ID used for an environment/deployment/play.
    """

    try:
        edp_ami_id = ec2.active_ami_for_edp(environment, deployment, play)
        if override:
            ami_id = override
        else:
            ami_id = edp_ami_id

        ami_info = {
            # This is passed directly to an ansible script that expects a base_ami_id variable
            'base_ami_id': ami_id,
            # This matches the key produced by the create_ami.yml ansible play to make
            # generating release pages easier.
            'ami_id': ami_id,
        }
        ami_info.update(ec2.tags_for_ami(edp_ami_id))
        logging.info("Found active AMI ID for {env}-{dep}-{play}: {ami_id}".format(
            env=environment, dep=deployment, play=play, ami_id=ami_id
        ))

        if out_file:
            with io.open(out_file, 'w') as stream:
                yaml.safe_dump(ami_info, stream, default_flow_style=False, explicit_start=True)
        else:
            print(yaml.safe_dump(ami_info, default_flow_style=False, explicit_start=True))

    except Exception as err:  # pylint: disable=broad-except
        traceback.print_exc()
        click.secho('Error finding base AMI ID.\nMessage: {}'.format(err), fg='red')
        sys.exit(1)

    sys.exit(0)

if __name__ == "__main__":
    retrieve_base_ami()  # pylint: disable=no-value-for-parameter
