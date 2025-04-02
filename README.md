# MCPVerse CLI

A command-line interface tool for interacting with MCP servers hosted on MCPVerse (https://mcpverse.dev).

## Installation

### Using Homebrew

```bash
brew tap village-chat/mcpverse
brew install mcpverse
```

## Usage

The CLI can be invoked with either `mcpverse` or the shorter alias `mcpv`.

### Authentication
Authenticate with browser:
```bash
mcpv auth login
```

Check current authentication status:
```bash
mcpv auth status
```

Log out
```bash
mcpv auth logout
```

### Proxy Command
Set up a local MCP proxy server to an MCPVerse server
```bash
mcpv proxy <URL>
```

## Development

### Setup

```bash
# Clone the repository
git clone https://github.com/village-chat/mcpverse-cli.git
cd mcpverse-cli

# Install in development mode
python3 -m venv .venv
source .venv/bin/activate
./install.sh
```

