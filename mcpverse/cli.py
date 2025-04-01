import click
import asyncio
from . import authentication
from . import stdio_proxy

@click.group()
def cli():
    """MCP CLI tool."""
    pass

@cli.command()
@click.argument('url')
def proxy(url):
    """Proxy URL command."""
    click.echo(f"Proxying to MCPverse server at {url}")
    if not authentication.is_authenticated():
        click.echo("Not logged in")
        return
    access_token = authentication.get_access_token()
    asyncio.run(stdio_proxy.run_proxy_stdio_server(url, access_token))

@cli.group()
def auth():
    """Authentication commands."""
    pass

@auth.command(name="login")
def auth_login():
    """Login to MCP via browser."""
    if authentication.is_authenticated():
        email = authentication.get_current_user_email()
        click.echo(f"Already logged in as {email}")
        return
    
    success, message = authentication.browser_login()
    if success:
        click.echo(f"Successfully logged in as {message}")
    else:
        click.echo(f"Login failed: {message}")

@auth.command(name="logout")
def auth_logout():
    """Logout from MCP."""
    if not authentication.is_authenticated():
        click.echo("Not logged in")
        return
    
    email = authentication.get_current_user_email()
    if authentication.remove_auth_info():
        click.echo(f"Successfully logged out from {email}")
    else:
        click.echo("Error logging out")

@auth.command(name="status")
def auth_status():
    """Check authentication status."""
    if authentication.is_authenticated():
        auth_data = authentication.get_auth_info()
        click.echo(f"Logged in as {auth_data.email}")
    else:
        click.echo("Not logged in")

def main():
    cli()

if __name__ == "__main__":
    main()
