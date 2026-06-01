import asyncio
import click
import importlib


_DB_MODULES = {
    'oracle':   'dbmd.ora.exporter.orchestrator',
    'postgres': 'dbmd.pg.exporter.orchestrator',
}


def _validate_name(ctx, param, value):
    if value == '':
        raise click.BadParameter('name cannot be empty')
    return value


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


def get_orchestrator(db: str, schema: str):
    module_path = _DB_MODULES.get(db)
    if not module_path:
        raise click.BadParameter(f"Unsupported DB type: '{db}'. Choose from: {', '.join(_DB_MODULES)}")

    module = importlib.import_module(module_path)
    return module.Orchestrator(schema)


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


@export.command('index', help='Export schema index')
@click.pass_context
def export_index(ctx):
    orchestrator = get_orchestrator(ctx.obj['db'], ctx.obj['schema'])
    asyncio.run(orchestrator.export_index())


@export.command('tables', help='Export tables')
@click.option('--name', default=None, callback=_validate_name, help='Export a single table by name')
@click.pass_context
def export_tables(ctx, name):
    orchestrator = get_orchestrator(ctx.obj['db'], ctx.obj['schema'])
    asyncio.run(orchestrator.export_tables(name=name))


@export.command('views', help='Export views')
@click.option('--name', default=None, callback=_validate_name, help='Export a single view by name')
@click.pass_context
def export_views(ctx, name):
    orchestrator = get_orchestrator(ctx.obj['db'], ctx.obj['schema'])
    asyncio.run(orchestrator.export_views(name=name))


@export.command('routines', help='Export standalone functions and procedures')
@click.option('--name', default=None, callback=_validate_name, help='Export a single routine by name')
@click.pass_context
def export_routines(ctx, name):
    orchestrator = get_orchestrator(ctx.obj['db'], ctx.obj['schema'])
    asyncio.run(orchestrator.export_routines(name=name))


@export.command('packages', help='Export packages (Oracle only)')
@click.option('--name', default=None, callback=_validate_name, help='Export a single package by name')
@click.pass_context
def export_packages(ctx, name):
    orchestrator = get_orchestrator(ctx.obj['db'], ctx.obj['schema'])
    if not hasattr(orchestrator, 'export_packages'):
        raise click.UsageError(f"'{ctx.obj['db']}' does not support packages")
    asyncio.run(orchestrator.export_packages(name=name))


@export.command('triggers', help='Export triggers')
@click.option('--name', default=None, callback=_validate_name, help='Export a single trigger by name')
@click.pass_context
def export_triggers(ctx, name):
    orchestrator = get_orchestrator(ctx.obj['db'], ctx.obj['schema'])
    asyncio.run(orchestrator.export_triggers(name=name))


@export.command('types', help='Export user-defined types')
@click.option('--name', default=None, callback=_validate_name, help='Export a single type by name')
@click.pass_context
def export_types(ctx, name):
    orchestrator = get_orchestrator(ctx.obj['db'], ctx.obj['schema'])
    asyncio.run(orchestrator.export_types(name=name))


if __name__ == '__main__':
    cli()
