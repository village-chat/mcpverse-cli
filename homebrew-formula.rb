class Mcpverse < Formula
  include Language::Python::Virtualenv

  desc "Command-line interface tool for MCPVerse"
  homepage "https://github.com/mcp/mcpverse-cli"
  url "https://files.pythonhosted.org/packages/source/m/mcpverse/mcpverse-0.1.0.tar.gz"
  sha256 "placeholder_sha256"  # You'll need to update this with the actual SHA once you have a release
  license "BSD-3-Clause"

  depends_on "python@3.8"

  def install
    virtualenv_install_with_resources
  end
end