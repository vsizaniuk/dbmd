import asyncio
import click

from dbmd.ora.exporter.orchestrator import Orchestrator as OraOrchestrator
from dbmd.pg.exporter.orchestrator import Orchestrator as PGOrchestrator


DB_ORCHESTRATORS = {
    'oracle':   OraOrchestrator,
    'postgres': PGOrchestrator,
}


class NestedHelpGroup(click.Group):
    def format_commands(self, ctx, formatter):
        commands = []
        for name, cmd in self.commands.items():
            if isinstance(cmd, click.Group):
                for sub_name, sub_cmd in cmd.commands.items():
                    commands.append((f'{name} {sub_name}', sub_cmd.get_short_help_str()))
            else:
                commands.append((name, cmd.get_short_help_str()))

        if commands:
            with formatter.section('Commands'):
                formatter.write_dl(commands)


def get_orchestrator(db: str, schema: str) -> OraOrchestrator | PGOrchestrator:
    cls = DB_ORCHESTRATORS.get(db)
    if not cls:
        raise click.BadParameter(f"Unsupported DB type: '{db}'. Choose from: {', '.join(DB_ORCHESTRATORS)}")
    return cls(schema)


@click.group(cls=NestedHelpGroup)
@click.option('--schema', default=None, help='DB schema to export (defaults to env var)')
@click.option('--db', default='oracle', show_default=True, help='Database type')
@click.pass_context
def cli(ctx, schema, db):
    ctx.ensure_object(dict)
    ctx.obj['schema'] = schema
    ctx.obj['db'] = db


@cli.group()
@click.pass_context
def export(ctx):
    pass


@export.command('all', help='Export all object types')
@click.pass_context
def export_all(ctx):
    orchestrator = get_orchestrator(ctx.obj['db'], ctx.obj['schema'])
    asyncio.run(orchestrator.export_all())


@export.command('tables', help='Export tables')
@click.pass_context
def export_tables(ctx):
    orchestrator = get_orchestrator(ctx.obj['db'], ctx.obj['schema'])
    asyncio.run(orchestrator.export_tables())


@export.command('views', help='Export views')
@click.pass_context
def export_views(ctx):
    orchestrator = get_orchestrator(ctx.obj['db'], ctx.obj['schema'])
    asyncio.run(orchestrator.export_views())


@export.command('routines', help='Export standalone functions and procedures')
@click.pass_context
def export_routines(ctx):
    orchestrator = get_orchestrator(ctx.obj['db'], ctx.obj['schema'])
    asyncio.run(orchestrator.export_routines())


@export.command('packages', help='Export packages (Oracle only)')
@click.pass_context
def export_packages(ctx):
    orchestrator = get_orchestrator(ctx.obj['db'], ctx.obj['schema'])
    if not hasattr(orchestrator, 'export_packages'):
        raise click.UsageError(f"'{ctx.obj['db']}' does not support packages")
    asyncio.run(orchestrator.export_packages())


@export.command('triggers', help='Export triggers')
@click.pass_context
def export_triggers(ctx):
    orchestrator = get_orchestrator(ctx.obj['db'], ctx.obj['schema'])
    asyncio.run(orchestrator.export_triggers())


@export.command('types', help='Export user-defined types')
@click.pass_context
def export_types(ctx):
    orchestrator = get_orchestrator(ctx.obj['db'], ctx.obj['schema'])
    asyncio.run(orchestrator.export_types())


if __name__ == '__main__':
    cli()
